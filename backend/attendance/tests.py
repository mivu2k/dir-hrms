from django.test import TestCase
from django.utils import timezone
import datetime
from employees.models import Company, Department, Designation, Employee
from attendance.models import Shift, AttendanceLog, AttendanceSummary, Holiday
from attendance.services import calculate_daily_summary

class AttendanceCalculationTestCase(TestCase):
    def setUp(self):
        # Create Company, Dept, Designation, Shift
        self.company = Company.objects.create(name="Test Corp", code="TC")
        self.dept = Department.objects.create(company=self.company, name="IT", code="ITD")
        self.desg = Designation.objects.create(department=self.dept, name="Engineer", code="ENG")
        self.shift = Shift.objects.create(
            name="Morning Shift",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
            grace_period_minutes=15,
            half_day_limit_minutes=120,
            early_exit_limit_minutes=15,
            min_hours_full_day=7.00,
            min_hours_half_day=3.50
        )
        
        # Create Employee
        self.employee = Employee.objects.create(
            employee_id="EMP-T01",
            first_name="Test",
            last_name="User",
            email="test.user@test.corp",
            shift=self.shift,
            joining_date=datetime.date(2026, 1, 1)
        )
        self.date = datetime.date(2026, 6, 16)

    def test_calculate_daily_summary_absent(self):
        """No punches should mark employee as ABSENT"""
        summary = calculate_daily_summary(self.employee, self.date)
        self.assertEqual(summary.status, 'ABSENT')
        self.assertEqual(summary.working_hours, 0.00)
        self.assertEqual(summary.late_minutes, 0)

    def test_calculate_daily_summary_present_on_time(self):
        """Punches matching standard shift hours should mark as PRESENT"""
        local_tz = timezone.get_current_timezone()
        # In-time 09:00 AM, Out-time 05:00 PM
        in_time = timezone.make_aware(datetime.datetime.combine(self.date, datetime.time(9, 0)), local_tz)
        out_time = timezone.make_aware(datetime.datetime.combine(self.date, datetime.time(17, 0)), local_tz)
        
        AttendanceLog.objects.create(employee=self.employee, timestamp=in_time, punch_type='CHECK_IN')
        AttendanceLog.objects.create(employee=self.employee, timestamp=out_time, punch_type='CHECK_OUT')
        
        summary = calculate_daily_summary(self.employee, self.date)
        self.assertEqual(summary.status, 'PRESENT')
        self.assertEqual(float(summary.working_hours), 8.00)
        self.assertEqual(summary.late_minutes, 0)
        self.assertEqual(summary.early_exit_minutes, 0)

    def test_calculate_daily_summary_late_arrival(self):
        """Punches after grace period should record late minutes"""
        local_tz = timezone.get_current_timezone()
        # In-time 09:30 AM (30 minutes late, beyond 15 minutes grace)
        in_time = timezone.make_aware(datetime.datetime.combine(self.date, datetime.time(9, 30)), local_tz)
        out_time = timezone.make_aware(datetime.datetime.combine(self.date, datetime.time(17, 30)), local_tz)
        
        AttendanceLog.objects.create(employee=self.employee, timestamp=in_time, punch_type='CHECK_IN')
        AttendanceLog.objects.create(employee=self.employee, timestamp=out_time, punch_type='CHECK_OUT')
        
        summary = calculate_daily_summary(self.employee, self.date)
        self.assertEqual(summary.status, 'PRESENT') # still worked 8 hours
        self.assertEqual(summary.late_minutes, 30)

    def test_calculate_daily_summary_holiday(self):
        """No punches on a public holiday should mark status as HOLIDAY"""
        Holiday.objects.create(date=self.date, name="Eid Holiday")
        
        summary = calculate_daily_summary(self.employee, self.date)
        self.assertEqual(summary.status, 'HOLIDAY')
        self.assertEqual(summary.working_hours, 0.00)

    def test_pull_users_api(self):
        """Simulate pulling users from device and verifying creation pipeline"""
        from devices.models import Device
        from leave.models import LeaveType
        
        # Ensure a default leave type exists
        LeaveType.objects.create(name="Annual Leave", code="AL", days_per_year=15)
        
        # Create a simulated device
        device = Device.objects.create(
            name="Test ZK",
            ip_address="192.168.1.250",
            port=4370,
            is_simulated=True,
            is_active=True
        )
        
        from devices.api import pull_users_from_device
        
        class MockRequest:
            def __init__(self):
                self.jwt_payload = {'role': 'SUPER_ADMIN', 'employee_id': 'EMP-T01'}
                
        req = MockRequest()
        res = pull_users_from_device(req, device.id)
        self.assertTrue(res['success'])
        self.assertGreater(res['imported_count'], 0)

    def test_portal_employee_creation_provisioning(self):
        """Creating an employee via the portal API should auto-provision salary structure and leave allocations"""
        from employees.api import create_employee
        from employees.schemas import EmployeeCreateSchema
        from leave.models import LeaveType, LeaveAllocation
        from payroll.models import SalaryStructure
        
        # Ensure a leave type exists
        LeaveType.objects.get_or_create(code="AL", defaults={"name": "Annual Leave", "days_per_year": 15})
        
        payload_data = {
            "employee_id": "EMP-PORTAL-01",
            "first_name": "Portal",
            "last_name": "User",
            "email": "portal.user@test.corp",
            "gender": "MALE",
            "marital_status": "SINGLE",
            "nationality": "Pakistani",
            "joining_date": datetime.date(2026, 6, 1),
            "shift_id": self.shift.id,
            "role": "EMPLOYEE",
            "status": "ACTIVE"
        }
        payload = EmployeeCreateSchema(**payload_data)
        
        class MockRequest:
            def __init__(self):
                self.jwt_payload = {'role': 'SUPER_ADMIN'}
                self.auth = None
                
        req = MockRequest()
        emp = create_employee(req, payload)
        
        # Check that employee was created
        self.assertIsNotNone(emp.id)
        self.assertEqual(emp.employee_id, "EMP-PORTAL-01")
        
        # Check that SalaryStructure was auto-created
        salary = SalaryStructure.objects.filter(employee=emp).first()
        self.assertIsNotNone(salary)
        self.assertEqual(float(salary.basic_salary), 45000.00)
        
        # Check that LeaveAllocation was auto-created
        allocation = LeaveAllocation.objects.filter(employee=emp, leave_type__code="AL", year=timezone.localdate().year).first()
        self.assertIsNotNone(allocation)
        self.assertEqual(float(allocation.allocated_days), 15.00)

    def test_payroll_generation_with_unpaid_leave_deduction(self):
        """Approved unpaid leave should deduct daily wage from payroll"""
        from leave.models import LeaveType, LeaveAllocation, LeaveRequest
        from payroll.models import SalaryStructure, Payroll, Payslip
        from payroll.api import generate_monthly_payroll
        
        # Create an unpaid leave type
        unpaid_leave_type, _ = LeaveType.objects.get_or_create(
            code="UPL",
            defaults={"name": "Unpaid Leave", "days_per_year": 10, "is_paid": False}
        )
        
        # Create Leave Allocation
        LeaveAllocation.objects.create(
            employee=self.employee,
            leave_type=unpaid_leave_type,
            year=self.date.year,
            allocated_days=10.0,
            used_days=0.0
        )
        
        # Create SalaryStructure for the employee
        SalaryStructure.objects.create(
            employee=self.employee,
            basic_salary=30000.00,  # 30,000 basic / 30 = 1,000 daily wage
            allowances=0.00,
            eobi_contribution=0.00,
            provident_fund=0.00,
            tax_percentage=0.00
        )
        
        # Request and approve unpaid leave for 2 days (June 16 to June 17, 2026)
        start_date = datetime.date(2026, 6, 16)
        end_date = datetime.date(2026, 6, 17)
        LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=unpaid_leave_type,
            start_date=start_date,
            end_date=end_date,
            reason="Unpaid leave test",
            status="APPROVED"
        )
        
        # Calculate daily summaries for the 2 days (should mark as ON_LEAVE)
        summary_16 = calculate_daily_summary(self.employee, start_date)
        summary_17 = calculate_daily_summary(self.employee, end_date)
        
        self.assertEqual(summary_16.status, 'ON_LEAVE')
        self.assertEqual(summary_17.status, 'ON_LEAVE')
        
        # Now generate monthly payroll for June 2026
        class MockRequest:
            def __init__(self):
                self.jwt_payload = {'role': 'SUPER_ADMIN'}
                self.auth = None
                
        req = MockRequest()
        res = generate_monthly_payroll(req, {"month": 6, "year": 2026})
        self.assertTrue(res['success'])
        
        # Verify Payslip has correct deduction
        # 2 days unpaid leave -> 2 * 1,000 = 2,000 deduction
        payslip = Payslip.objects.filter(employee=self.employee, payroll__month=6, payroll__year=2026).first()
        self.assertIsNotNone(payslip)
        self.assertEqual(float(payslip.leave_deduction), 2000.00)
        self.assertEqual(float(payslip.net_salary), 28000.00) # 30,000 - 2,000 = 28,000

