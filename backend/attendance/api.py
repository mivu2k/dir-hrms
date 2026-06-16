import datetime
from datetime import date
from typing import List
from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from api.security import JWTAuth
from employees.models import Employee
from attendance.models import Shift, AttendanceLog, AttendanceSummary, AttendanceCorrectionRequest, Holiday
from attendance.schemas import (
    ShiftSchema, ShiftCreateSchema,
    AttendanceLogSchema, AttendanceLogCreateSchema,
    AttendanceSummarySchema,
    AttendanceCorrectionRequestSchema, AttendanceCorrectionCreateSchema,
    HolidaySchema
)
from attendance.services import calculate_daily_summary

attendance_router = Router(tags=["Attendance Management"], auth=JWTAuth())

# ================= SHIFT CRUD =================

@attendance_router.get("/shifts", response=List[ShiftSchema])
def list_shifts(request):
    return Shift.objects.all()


@attendance_router.post("/shifts", response=ShiftSchema)
def create_shift(request, data: ShiftCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
    shift = Shift.objects.create(**data.dict())
    return shift

# ================= SELF WEB / GPS PUNCH =================

@attendance_router.post("/punch", response=dict)
def web_punch(request, data: AttendanceLogCreateSchema):
    """
    Simulates a web or GPS check-in/out punch from the self-service dashboard.
    Automatically recalculates the daily attendance summary.
    """
    user = request.auth
    try:
        employee = Employee.objects.get(user=user, status='ACTIVE')
    except Employee.DoesNotExist:
        raise HttpError(404, "Active employee profile not found.")

    now = timezone.now()
    
    # Check if punch already exists at exact time (rare, but prevents double punch)
    log, created = AttendanceLog.objects.get_or_create(
        employee=employee,
        timestamp=now,
        defaults={
            'punch_type': data.punch_type,
            'verification_mode': data.verification_mode,
            'latitude': data.latitude,
            'longitude': data.longitude
        }
    )
    
    # Recalculate for today
    today = timezone.localtime(now).date()
    calculate_daily_summary(employee, today)
    
    return {
        "success": True, 
        "message": f"Successfully punched {data.punch_type} at {timezone.localtime(now).strftime('%I:%M:%S %p')}",
        "timestamp": now
    }

# ================= RAW ATTENDANCE LOGS =================

@attendance_router.get("/logs", response=List[AttendanceLogSchema])
def list_logs(request, employee_id: int = None, start_date: date = None, end_date: date = None):
    queryset = AttendanceLog.objects.all()
    
    # Role checks
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        # Filter strictly for own logs if not admin
        queryset = queryset.filter(employee_id=curr_emp_id)
    elif employee_id:
        queryset = queryset.filter(employee_id=employee_id)
        
    if start_date and end_date:
        local_tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min), local_tz)
        end_dt = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max), local_tz)
        queryset = queryset.filter(timestamp__range=(start_dt, end_dt))
        
    return queryset[:100]

# ================= DAILY ATTENDANCE SUMMARIES =================

@attendance_router.get("/summaries", response=List[AttendanceSummarySchema])
def list_summaries(request, employee_id: int = None, department_id: int = None, start_date: date = None, end_date: date = None, status: str = None):
    queryset = AttendanceSummary.objects.select_related('employee', 'employee__department').all()
    
    # Role checks
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'ACCOUNTANT', 'DEPT_MANAGER']:
        # Normal employees only see their own summaries
        queryset = queryset.filter(employee_id=curr_emp_id)
    else:
        # Managers filter
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
            
    if start_date and end_date:
        queryset = queryset.filter(date__range=(start_date, end_date))
    if status:
        queryset = queryset.filter(status=status)
        
    return queryset

# ================= ATTENDANCE REGULARIZATION (CORRECTIONS) =================

@attendance_router.get("/corrections", response=List[AttendanceCorrectionRequestSchema])
def list_correction_requests(request):
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    if role in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'DEPT_MANAGER']:
        return AttendanceCorrectionRequest.objects.all()
    else:
        return AttendanceCorrectionRequest.objects.filter(employee_id=curr_emp_id)


@attendance_router.post("/corrections", response=AttendanceCorrectionRequestSchema)
def submit_correction_request(request, data: AttendanceCorrectionCreateSchema):
    try:
        employee = Employee.objects.get(user=request.auth, status='ACTIVE')
    except Employee.DoesNotExist:
        raise HttpError(404, "Employee not found.")
        
    # Check if duplicate request exists
    if AttendanceCorrectionRequest.objects.filter(employee=employee, date=data.date, status='PENDING').exists():
        raise HttpError(400, f"Pending correction request already exists for {data.date}")
        
    corr = AttendanceCorrectionRequest.objects.create(
        employee=employee,
        date=data.date,
        requested_check_in=data.requested_check_in,
        requested_check_out=data.requested_check_out,
        reason=data.reason,
        status='PENDING'
    )
    return corr


@attendance_router.post("/corrections/{request_id}/approve", response=dict)
def approve_correction_request(request, request_id: int, payload: dict):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'DEPT_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        corr = AttendanceCorrectionRequest.objects.get(id=request_id, status='PENDING')
    except AttendanceCorrectionRequest.DoesNotExist:
        raise HttpError(404, "Pending correction request not found")
        
    approver = Employee.objects.get(user=request.auth)
    local_tz = timezone.get_current_timezone()
    
    with transaction.atomic():
        corr.status = 'APPROVED'
        corr.approved_by = approver
        corr.comments = payload.get("comments", "")
        corr.save()
        
        # Inject logs representing the corrected times
        if corr.requested_check_in:
            dt_in = timezone.make_aware(datetime.datetime.combine(corr.date, corr.requested_check_in), local_tz)
            AttendanceLog.objects.get_or_create(
                employee=corr.employee,
                timestamp=dt_in,
                defaults={'punch_type': 'CHECK_IN', 'verification_mode': 'MANUAL'}
            )
            
        if corr.requested_check_out:
            dt_out = timezone.make_aware(datetime.datetime.combine(corr.date, corr.requested_check_out), local_tz)
            AttendanceLog.objects.get_or_create(
                employee=corr.employee,
                timestamp=dt_out,
                defaults={'punch_type': 'CHECK_OUT', 'verification_mode': 'MANUAL'}
            )
            
        # Recompute daily summary
        calculate_daily_summary(corr.employee, corr.date)
        
    return {"success": True, "message": "Correction request approved and summaries updated."}


@attendance_router.post("/corrections/{request_id}/reject", response=dict)
def reject_correction_request(request, request_id: int, payload: dict):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'DEPT_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        corr = AttendanceCorrectionRequest.objects.get(id=request_id, status='PENDING')
    except AttendanceCorrectionRequest.DoesNotExist:
        raise HttpError(404, "Pending correction request not found")
        
    approver = Employee.objects.get(user=request.auth)
    
    corr.status = 'REJECTED'
    corr.approved_by = approver
    corr.comments = payload.get("comments", "")
    corr.save()
    
    return {"success": True, "message": "Correction request rejected."}

# ================= HOLIDAYS CRUD =================

@attendance_router.get("/holidays", response=List[HolidaySchema])
def list_holidays(request):
    return Holiday.objects.all()


@attendance_router.post("/holidays", response=HolidaySchema)
def create_holiday(request, data: HolidaySchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
    holiday = Holiday.objects.create(
        name=data.name,
        date=data.date,
        description=data.description
    )
    return holiday
