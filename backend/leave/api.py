from typing import List
import datetime
from django.db import transaction
from ninja import Router
from ninja.errors import HttpError
from api.security import JWTAuth
from employees.models import Employee
from leave.models import LeaveType, LeaveAllocation, LeaveRequest
from leave.schemas import LeaveTypeSchema, LeaveAllocationSchema, LeaveRequestSchema, LeaveRequestCreateSchema
from attendance.services import calculate_daily_summary

leave_router = Router(tags=["Leave Management"], auth=JWTAuth())

# ================= LEAVE TYPES =================

@leave_router.get("/types", response=List[LeaveTypeSchema])
def list_leave_types(request):
    return LeaveType.objects.all()

# ================= LEAVE BALANCE / ALLOCATIONS =================

@leave_router.get("/balances", response=List[LeaveAllocationSchema])
def list_balances(request, employee_id: int = None):
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    year = datetime.date.today().year

    queryset = LeaveAllocation.objects.select_related('employee', 'leave_type').filter(year=year)
    
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'ACCOUNTANT']:
        # Employees only see their own balances
        return queryset.filter(employee_id=curr_emp_id)
        
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
        
    return queryset

# ================= LEAVE REQUESTS & WORKFLOW =================

@leave_router.get("/requests", response=List[LeaveRequestSchema])
def list_leave_requests(request):
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    if role in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        return LeaveRequest.objects.all()
    elif role == 'DEPT_MANAGER':
        # Department managers see their department's requests + own
        return LeaveRequest.objects.filter(employee__department__employees__manager_id=curr_emp_id).distinct()
    else:
        return LeaveRequest.objects.filter(employee_id=curr_emp_id)


@leave_router.post("/requests", response=LeaveRequestSchema)
def submit_leave_request(request, data: LeaveRequestCreateSchema):
    try:
        employee = Employee.objects.get(user=request.auth, status='ACTIVE')
    except Employee.DoesNotExist:
        raise HttpError(404, "Active employee profile not found.")
        
    if data.start_date > data.end_date:
        raise HttpError(400, "Start date cannot be after end date.")
        
    # Calculate days requested
    total_days = (data.end_date - data.start_date).days + 1
    year = data.start_date.year
    
    try:
        leave_type = LeaveType.objects.get(id=data.leave_type_id)
    except LeaveType.DoesNotExist:
        raise HttpError(404, "Leave type not found.")
        
    # Check leave allocation / balance
    allocation, created = LeaveAllocation.objects.get_or_create(
        employee=employee,
        leave_type=leave_type,
        year=year,
        defaults={'allocated_days': leave_type.days_per_year, 'used_days': 0.00}
    )
    
    available = float(allocation.allocated_days) - float(allocation.used_days)
    if total_days > available:
        raise HttpError(400, f"Insufficient leave balance. Requested: {total_days}, Available: {available}")
        
    # Create request
    leave_req = LeaveRequest.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status='PENDING'
    )
    return leave_req


@leave_router.post("/requests/{req_id}/approve", response=dict)
def approve_leave_request(request, req_id: int, payload: dict):
    """
    Multi-tier Approval Workflow:
    1. Employee submits request (PENDING).
    2. Manager approves (MANAGER_APPROVED).
    3. HR Manager approves (APPROVED).
    Upon HR approval, balances are deducted, and summaries recalculated.
    """
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    try:
        leave_req = LeaveRequest.objects.get(id=req_id)
    except LeaveRequest.DoesNotExist:
        raise HttpError(404, "Leave request not found.")
        
    if leave_req.status in ['APPROVED', 'REJECTED']:
        raise HttpError(400, f"Leave request is already {leave_req.status}.")
        
    approver = Employee.objects.get(user=request.auth)
    comments = payload.get("comments", "")
    
    with transaction.atomic():
        if leave_req.status == 'PENDING':
            # 1. Manager tier approval
            # Allowed for SUPER_ADMIN, HR_MANAGER, or the employee's direct manager
            is_manager = leave_req.employee.manager_id == curr_emp_id
            if role not in ['SUPER_ADMIN', 'HR_MANAGER'] and not is_manager:
                raise HttpError(403, "Only the direct manager or HR can perform the first level approval.")
                
            leave_req.status = 'MANAGER_APPROVED'
            leave_req.manager_approved_by = approver
            leave_req.comments = comments
            leave_req.save()
            return {"success": True, "message": "Leave request approved by Manager. Pending HR confirmation."}
            
        elif leave_req.status == 'MANAGER_APPROVED':
            # 2. HR tier approval (Final)
            if role not in ['SUPER_ADMIN', 'HR_MANAGER']:
                raise HttpError(403, "Only HR Managers/Super Admins can perform final approval.")
                
            leave_req.status = 'APPROVED'
            leave_req.hr_approved_by = approver
            leave_req.comments = comments
            leave_req.save()
            
            # Deduct balance
            year = leave_req.start_date.year
            allocation = LeaveAllocation.objects.get(
                employee=leave_req.employee,
                leave_type=leave_req.leave_type,
                year=year
            )
            allocation.used_days = float(allocation.used_days) + float(leave_req.total_days)
            allocation.save()
            
            # Recalculate attendance summaries for all dates in range
            start = leave_req.start_date
            end = leave_req.end_date
            curr = start
            while curr <= end:
                calculate_daily_summary(leave_req.employee, curr)
                curr += datetime.timedelta(days=1)
                
            return {"success": True, "message": "Leave request approved by HR and balance updated."}
            
    return {"success": False, "message": "Unknown request state."}


@leave_router.post("/requests/{req_id}/reject", response=dict)
def reject_leave_request(request, req_id: int, payload: dict):
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    try:
        leave_req = LeaveRequest.objects.get(id=req_id)
    except LeaveRequest.DoesNotExist:
        raise HttpError(404, "Leave request not found.")
        
    if leave_req.status in ['APPROVED', 'REJECTED']:
        raise HttpError(400, "Leave request is already finalized.")
        
    approver = Employee.objects.get(user=request.auth)
    
    # Check permissions
    is_manager = leave_req.employee.manager_id == curr_emp_id
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER'] and not is_manager:
        raise HttpError(403, "Permission Denied")
        
    leave_req.status = 'REJECTED'
    if leave_req.status == 'PENDING':
        leave_req.manager_approved_by = approver
    else:
        leave_req.hr_approved_by = approver
    leave_req.comments = payload.get("comments", "Rejected")
    leave_req.save()
    
    return {"success": True, "message": "Leave request rejected."}
