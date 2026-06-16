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
            min_hours_full_day=8.00,
            min_hours_half_day=4.00
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
