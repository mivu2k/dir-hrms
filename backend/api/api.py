from django.utils import timezone
import datetime
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from api.security import JWTAuth
from employees.models import Employee
from devices.models import Device, DeviceLog
from attendance.models import AttendanceLog, AttendanceSummary, Holiday
from leave.models import LeaveRequest
from payroll.models import Payroll, Payslip
from employees.api import auth_router, employee_router
from devices.api import device_router
from attendance.api import attendance_router
from leave.api import leave_router
from payroll.api import payroll_router

# Initialize the main NinjaAPI instance
api = NinjaAPI(
    title="HRMS & Biometric Attendance API",
    version="1.0.0",
    description="Backend API for the Human Resource Management System with ZKTeco biometric integration.",
)

# Register app routers
api.add_router("/auth", auth_router)
api.add_router("/employees", employee_router)
api.add_router("/devices", device_router)
api.add_router("/attendance", attendance_router)
api.add_router("/leave", leave_router)
api.add_router("/payroll", payroll_router)

# ================= DASHBOARD SUMMARY ENDPOINT =================

dashboard_router = Router(tags=["Dashboard"], auth=JWTAuth())

@dashboard_router.get("/summary", response=dict)
def get_dashboard_summary(request):
    """
    Returns consolidated statistics for the dashboard:
    - Active employee metrics (Present, Late, Absent, On Leave)
    - Device health statuses
    - Recent activities
    - Biometric stats
    """
    today = timezone.localdate()
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    # Active employee count
    total_employees = Employee.objects.filter(status='ACTIVE').count()
    
    # Summaries for today
    today_summaries = AttendanceSummary.objects.filter(date=today)
    
    present_today = today_summaries.filter(status='PRESENT').count()
    absent_today = today_summaries.filter(status='ABSENT').count()
    half_day_today = today_summaries.filter(status='HALF_DAY').count()
    on_leave_today = today_summaries.filter(status='ON_LEAVE').count()
    late_today = today_summaries.filter(late_minutes__gt=0).count()
    
    # Defaults in case log calculation hasn't run yet for all
    if today_summaries.count() == 0 and total_employees > 0:
        # If no summaries exist yet, absent count is total active
        absent_today = total_employees

    # Device counts
    active_devices = Device.objects.filter(is_active=True)
    devices_online = active_devices.filter(connection_status='ONLINE').count()
    devices_offline = active_devices.filter(connection_status='OFFLINE').count()
    
    # Recent punches (last 10)
    # Admin roles see all, employee sees only own
    recent_punches = []
    punches_qs = AttendanceLog.objects.select_related('employee')
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        punches_qs = punches_qs.filter(employee_id=curr_emp_id)
        
    for punch in punches_qs[:10]:
        recent_punches.append({
            "employee_id": punch.employee.employee_id,
            "employee_name": f"{punch.employee.first_name} {punch.employee.last_name}",
            "timestamp": timezone.localtime(punch.timestamp).strftime('%Y-%m-%d %I:%M:%S %p'),
            "punch_type": punch.punch_type,
            "verification_mode": punch.verification_mode
        })
        
    # Pending approval counts
    pending_leaves = LeaveRequest.objects.filter(status='PENDING').count()
    pending_corrections = AttendanceCorrectionRequestSchema = 0
    if role in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        from attendance.models import AttendanceCorrectionRequest
        pending_corrections = AttendanceCorrectionRequest.objects.filter(status='PENDING').count()
        
    # Payroll Summary (last calculated payroll net payout)
    last_payroll = Payroll.objects.filter(status='APPROVED').first()
    payout_summary = None
    if last_payroll and role in ['SUPER_ADMIN', 'HR_MANAGER', 'ACCOUNTANT']:
        payslips = Payslip.objects.filter(payroll=last_payroll)
        payout_summary = {
            "month_year": f"{last_payroll.year}-{last_payroll.month:02d}",
            "payslips_count": payslips.count(),
            "total_net_payout": float(sum(p.net_salary for p in payslips))
        }

    return {
        "metrics": {
            "total_employees": total_employees,
            "present_today": present_today + half_day_today,
            "absent_today": absent_today,
            "late_today": late_today,
            "on_leave_today": on_leave_today
        },
        "devices": {
            "total": active_devices.count(),
            "online": devices_online,
            "offline": devices_offline
        },
        "alerts": {
            "pending_leaves": pending_leaves,
            "pending_corrections": pending_corrections
        },
        "recent_punches": recent_punches,
        "payroll_summary": payout_summary
    }

# Register dashboard router
api.add_router("/dashboard", dashboard_router)
