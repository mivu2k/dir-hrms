from typing import List
import datetime
from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from api.security import JWTAuth
from employees.models import Employee
from attendance.models import AttendanceSummary
from payroll.models import SalaryStructure, Payroll, Payslip
from payroll.schemas import SalaryStructureSchema, SalaryStructureUpdateSchema, PayrollSchema, PayslipSchema

payroll_router = Router(tags=["Payroll Management"], auth=JWTAuth())

# ================= SALARY STRUCTURES =================

@payroll_router.get("/salary-structures/{employee_id}", response=SalaryStructureSchema)
def get_salary_structure(request, employee_id: int):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'ACCOUNTANT']:
        raise HttpError(403, "Permission Denied")
        
    try:
        structure = SalaryStructure.objects.select_related('employee').get(employee_id=employee_id)
        return structure
    except SalaryStructure.DoesNotExist:
        # If none exists, return a dummy or raise 404
        # For ease of creation, we can default it or return 404
        raise HttpError(404, "Salary structure not configured for this employee.")


@payroll_router.post("/salary-structures/{employee_id}", response=SalaryStructureSchema)
def configure_salary_structure(request, employee_id: int, data: SalaryStructureUpdateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise HttpError(404, "Employee not found")
        
    structure, created = SalaryStructure.objects.update_or_create(
        employee=employee,
        defaults=data.dict()
    )
    return structure

# ================= MONTHLY PAYROLL PROCESSING =================

@payroll_router.get("/payrolls", response=List[PayrollSchema])
def list_payrolls(request):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'ACCOUNTANT']:
        raise HttpError(403, "Permission Denied")
    return Payroll.objects.all()


@payroll_router.post("/payrolls/generate", response=dict)
def generate_monthly_payroll(request, payload: dict):
    """
    Generates monthly payroll for a given month and year.
    Processes basic salary, allowances, overtime, late arrival deductions,
    absent day deductions, tax, and EOBI/PF deductions.
    """
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'ACCOUNTANT']:
        raise HttpError(403, "Permission Denied")
        
    month = payload.get("month")
    year = payload.get("year")
    
    if not month or not year:
        raise HttpError(400, "Month and year are required.")
        
    # Get active employees who have a salary structure
    employees = Employee.objects.filter(status='ACTIVE', salary_structure__isnull=False)
    if not employees.exists():
        raise HttpError(400, "No active employees found with configured salary structures.")
        
    with transaction.atomic():
        # Create or update payroll record (draft)
        payroll, created = Payroll.objects.get_or_create(
            month=month,
            year=year,
            defaults={'status': 'DRAFT'}
        )
        
        # If payroll is already approved/paid, block regeneration
        if payroll.status != 'DRAFT':
            raise HttpError(400, f"Payroll for {year}-{month:02d} is already finalized and cannot be regenerated.")
            
        payslips_count = 0
        total_net_payout = 0.00
        
        # Process each employee
        for emp in employees:
            struct = emp.salary_structure
            basic = struct.basic_salary
            allowances = struct.allowances
            
            # Fetch daily summaries for the month
            start_date = datetime.date(year, month, 1)
            # Find last day of month
            if month == 12:
                end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
                
            summaries = AttendanceSummary.objects.filter(
                employee=emp,
                date__range=(start_date, end_date)
            )
            
            # 1. Calculate Absent and Unpaid Leave Days Deduction
            # Daily Wage = Basic Salary / 30
            from decimal import Decimal
            daily_wage = basic / 30
            absent_days = summaries.filter(status='ABSENT').count()
            half_days = summaries.filter(status='HALF_DAY').count()
            
            # Count days on unpaid leave
            from leave.models import LeaveRequest
            unpaid_leave_days = 0
            on_leave_summaries = summaries.filter(status='ON_LEAVE')
            for summary in on_leave_summaries:
                leave_req = LeaveRequest.objects.filter(
                    employee=emp,
                    start_date__lte=summary.date,
                    end_date__gte=summary.date,
                    status='APPROVED'
                ).select_related('leave_type').first()
                if leave_req and not leave_req.leave_type.is_paid:
                    unpaid_leave_days += 1
            
            leave_multiplier = Decimal(absent_days) + (Decimal(half_days) * Decimal('0.5')) + Decimal(unpaid_leave_days)
            leave_deduction = daily_wage * leave_multiplier
            
            # 2. Calculate Late Arrival Deduction (e.g. 10% daily wage per late arrival after grace)
            late_arrivals = summaries.filter(late_minutes__gt=0).count()
            late_deduction = daily_wage * Decimal('0.10') * Decimal(late_arrivals)
            
            # 3. Calculate Overtime (e.g. 1.5x hourly rate)
            # Hourly Rate = Daily Wage / (daily shift hours, default 7)
            shift = emp.shift
            shift_hours = shift.min_hours_full_day if shift else Decimal('7.00')
            hourly_rate = daily_wage / shift_hours
            overtime_min = sum(summary.overtime_minutes for summary in summaries)
            overtime_hours = Decimal(overtime_min) / Decimal('60.0')
            overtime_amount = hourly_rate * Decimal('1.5') * overtime_hours
            
            # 4. Tax Deduction
            tax_deduction = basic * (struct.tax_percentage / 100)
            
            # EOBI & PF Deductions
            eobi_deduction = struct.eobi_contribution
            pf_deduction = struct.provident_fund
            
            # Net Salary
            net = (basic + allowances + overtime_amount) - (leave_deduction + late_deduction + tax_deduction + eobi_deduction + pf_deduction)
            # Prevent negative salary
            net = max(Decimal('0.00'), net)
            
            # Create or update payslip
            payslip, _ = Payslip.objects.update_or_create(
                payroll=payroll,
                employee=emp,
                defaults={
                    'basic_salary': basic,
                    'allowances': allowances,
                    'overtime_amount': overtime_amount,
                    'bonus': 0.00, # Can be manual
                    'late_deduction': late_deduction,
                    'leave_deduction': leave_deduction,
                    'tax_deduction': tax_deduction,
                    'eobi_deduction': eobi_deduction,
                    'provident_fund_deduction': pf_deduction,
                    'net_salary': net,
                    'status': 'DRAFT'
                }
            )
            
            payslips_count += 1
            total_net_payout += float(net)
            
    return {
        "success": True,
        "message": f"Successfully generated {payslips_count} payslips for {year}-{month:02d}.",
        "payroll_id": payroll.id,
        "payslips_count": payslips_count,
        "total_net_payout": round(total_net_payout, 2)
    }


@payroll_router.post("/payrolls/{payroll_id}/approve", response=dict)
def approve_payroll(request, payroll_id: int):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        payroll = Payroll.objects.get(id=payroll_id, status='DRAFT')
    except Payroll.DoesNotExist:
        raise HttpError(404, "Draft payroll not found.")
        
    approver = Employee.objects.get(user=request.auth)
    
    with transaction.atomic():
        payroll.status = 'APPROVED'
        payroll.approved_at = timezone.now()
        payroll.approved_by = approver
        payroll.save()
        
        # Approve all associated payslips
        Payslip.objects.filter(payroll=payroll).update(status='PAID')
        
    return {"success": True, "message": f"Payroll {payroll.year}-{payroll.month:02d} approved successfully."}

# ================= PAYSLIPS ACCESS =================

@payroll_router.get("/payslips", response=List[PayslipSchema])
def list_payslips(request, payroll_id: int = None):
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    queryset = Payslip.objects.select_related('payroll', 'employee', 'employee__department').all()
    
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'ACCOUNTANT']:
        # Filter for own payslips
        queryset = queryset.filter(employee_id=curr_emp_id, payroll__status='APPROVED')
    elif payroll_id:
        queryset = queryset.filter(payroll_id=payroll_id)
        
    return queryset


@payroll_router.get("/payslips/{payslip_id}", response=PayslipSchema)
def get_payslip(request, payslip_id: int):
    role = request.jwt_payload['role']
    curr_emp_id = request.jwt_payload.get('employee_id')
    
    try:
        payslip = Payslip.objects.select_related('payroll', 'employee').get(id=payslip_id)
    except Payslip.DoesNotExist:
        raise HttpError(404, "Payslip not found.")
        
    if role not in ['SUPER_ADMIN', 'HR_MANAGER', 'ACCOUNTANT'] and payslip.employee.id != curr_emp_id:
        raise HttpError(403, "Permission Denied")
        
    return payslip
