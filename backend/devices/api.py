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

