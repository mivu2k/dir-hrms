from typing import List
from ninja import Router
from ninja.errors import HttpError
from api.security import JWTAuth
from devices.models import Device, DeviceLog
from devices.schemas import DeviceSchema, DeviceCreateSchema, DeviceLogSchema
from devices.services.zk_service import ZKService
from devices.tasks import sync_device_attendance

device_router = Router(tags=["Biometric Devices"], auth=JWTAuth())

@device_router.get("/", response=List[DeviceSchema])
def list_devices(request):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        raise HttpError(403, "Permission Denied")
    return Device.objects.all()


@device_router.post("/", response=DeviceSchema)
def create_device(request, data: DeviceCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
    
    device = Device.objects.create(**data.dict())
    return device


@device_router.put("/{device_id}", response=DeviceSchema)
def update_device(request, device_id: int, data: DeviceCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise HttpError(404, "Device not found")
        
    for attr, val in data.dict().items():
        setattr(device, attr, val)
    device.save()
    return device


@device_router.delete("/{device_id}", response=dict)
def delete_device(request, device_id: int):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        device = Device.objects.get(id=device_id)
        device.delete()
        return {"success": True, "message": f"Device {device_id} deleted successfully"}
    except Device.DoesNotExist:
        raise HttpError(404, "Device not found")


@device_router.post("/{device_id}/test", response=dict)
def test_device_connection(request, device_id: int):
    """
    Connects to the ZKTeco device, fetches health data, and logs the result.
    Returns status info.
    """
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise HttpError(404, "Device not found")
        
    zk = ZKService(device)
    if zk.connect():
        try:
            health = zk.get_health()
            zk.disconnect()
            return {
                "success": True,
                "message": "Connection tested successfully.",
                "details": health
            }
        except Exception as e:
            zk.disconnect()
            return {
                "success": False,
                "message": f"Connection succeeded but failed to fetch health parameters: {str(e)}"
            }
    else:
        return {
            "success": False,
            "message": f"Failed to connect to device at {device.ip_address}:{device.port}. Check DeviceLogs for details."
        }


@device_router.post("/{device_id}/sync", response=dict)
def trigger_device_sync(request, device_id: int):
    """
    Manually triggers log synchronization for the device.
    Uses the Celery task synchronously for immediate response.
    """
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        raise HttpError(403, "Permission Denied")
        
    # Trigger task synchronously
    result = sync_device_attendance(device_id)
    return result


@device_router.get("/{device_id}/logs", response=List[DeviceLogSchema])
def get_device_logs(request, device_id: int, limit: int = 50):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise HttpError(404, "Device not found")
        
    return DeviceLog.objects.filter(device=device)[:limit]


@device_router.post("/clear-mock-data", response=dict)
def clear_mock_data(request):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    from django.db.models import Q
    from attendance.models import AttendanceLog, AttendanceSummary
    
    # 1. Delete all device logs for simulated devices
    device_logs_deleted, _ = DeviceLog.objects.filter(device__is_simulated=True).delete()
    
    # 2. Delete all attendance logs from simulated devices (or where device was deleted/null)
    logs_deleted, _ = AttendanceLog.objects.filter(Q(device__is_simulated=True) | Q(device__isnull=True)).delete()
    
    # 3. Delete all summaries since they were computed from mock data
    summaries_deleted, _ = AttendanceSummary.objects.all().delete()
    
    return {
        "success": True, 
        "message": f"Successfully deleted mock data: {logs_deleted} logs, {device_logs_deleted} sync logs, and {summaries_deleted} summaries."
    }


@device_router.post("/{device_id}/pull-users", response=dict)
def pull_users_from_device(request, device_id: int):
    """
    Pulls all users registered on the biometric device.
    Registers employees, salary structures, and leave allocations for those not in the DB.
    """
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        device = Device.objects.get(id=device_id, is_active=True)
    except Device.DoesNotExist:
        raise HttpError(404, "Device not found or inactive")
        
    zk = ZKService(device)
    if not zk.connect():
        raise HttpError(400, f"Failed to connect to device {device.name}")
        
    try:
        users = zk.get_users()
        imported_count = 0
        skipped_count = 0
        
        import random
        from django.utils import timezone
        from django.contrib.auth.models import User
        from employees.models import Employee, Department, Designation
        from attendance.models import Shift
        from payroll.models import SalaryStructure
        from leave.models import LeaveType, LeaveAllocation
        
        # Get defaults
        default_dept = Department.objects.first()
        default_desg = Designation.objects.first()
        default_shift = Shift.objects.filter(is_active=True).first()
        
        # Determine leave types
        active_leave_types = LeaveType.objects.all()
        current_year = timezone.localdate().year
        
        for u in users:
            bio_id = str(u.user_id)
            
            # Check if employee with this bio ID already exists
            if Employee.objects.filter(bio_device_user_id=bio_id).exists():
                skipped_count += 1
                continue
                
            # If not exists, create user & employee
            # Parse names
            name_parts = u.name.strip().split(None, 1)
            first_name = name_parts[0] if name_parts else f"ZK-{bio_id}"
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Generate unique employee ID
            emp_id = f"EMP-ZK-{bio_id.zfill(3)}"
            while Employee.objects.filter(employee_id=emp_id).exists():
                emp_id = f"EMP-ZK-{bio_id.zfill(3)}-{random.randint(10, 99)}"
                
            # Generate unique email
            email_prefix = f"{first_name.lower().replace(' ', '')}.{bio_id}"
            email = f"{email_prefix}@antigravity.corp"
            while Employee.objects.filter(email=email).exists():
                email = f"{email_prefix}{random.randint(10, 99)}@antigravity.corp"
                
            # Create a matching Django auth User
            username = f"user_{bio_id}"
            while User.objects.filter(username=username).exists():
                username = f"user_{bio_id}_{random.randint(10, 99)}"
                
            user_obj = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,
                is_superuser=False
            )
            user_obj.set_password("user123")
            user_obj.save()
            
            # Create Employee Profile
            employee = Employee.objects.create(
                user=user_obj,
                employee_id=emp_id,
                bio_device_user_id=bio_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                joining_date=timezone.localdate(),
                status='ACTIVE',
                role='EMPLOYEE',
                department=default_dept,
                designation=default_desg,
                shift=default_shift
            )
            
            # Create Default Salary Structure (essential for running payroll later)
            SalaryStructure.objects.create(
                employee=employee,
                basic_salary=45000.00,
                allowances=5000.00,
                eobi_contribution=1000.00,
                provident_fund=1500.00,
                tax_percentage=0.00
            )
            
            # Allocate Leaves
            for lt in active_leave_types:
                LeaveAllocation.objects.create(
                    employee=employee,
                    leave_type=lt,
                    year=current_year,
                    allocated_days=lt.days_per_year,
                    used_days=0.00
                )
                
            imported_count += 1
            
        return {
            "success": True,
            "message": f"Successfully pulled users from device. Registered {imported_count} new employees (with salary and leave templates), skipped {skipped_count} existing.",
            "imported_count": imported_count,
            "skipped_count": skipped_count
        }
    except Exception as e:
        raise HttpError(400, f"Error pulling users from device: {str(e)}")
    finally:
        zk.disconnect()


