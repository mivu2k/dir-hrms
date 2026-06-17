import datetime
from django.utils import timezone
from employees.models import Employee
from attendance.models import Shift, AttendanceLog, AttendanceSummary, Holiday
from leave.models import LeaveRequest

def calculate_daily_summary(employee: Employee, date: datetime.date) -> AttendanceSummary:
    """
    Consolidates raw attendance punches for an employee on a specific date,
    calculates late minutes, early exit, working hours, overtime, and final status.
    """
    # Define start and end of day in timezone-aware format
    local_tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.datetime.combine(date, datetime.time.min), local_tz)
    end_dt = timezone.make_aware(datetime.datetime.combine(date, datetime.time.max), local_tz)

    # Fetch logs for this employee on this date
    logs = AttendanceLog.objects.filter(
        employee=employee,
        timestamp__range=(start_dt, end_dt)
    ).order_by('timestamp')

    # Fetch default shift or employee shift
    shift = employee.shift
    if not shift:
        # Fallback to a default shift (09:00 to 17:00)
        shift, _ = Shift.objects.get_or_create(
            name="Default Shift",
            defaults={
                'start_time': datetime.time(9, 0),
                'end_time': datetime.time(17, 0),
                'grace_period_minutes': 15,
                'half_day_limit_minutes': 120,
                'early_exit_limit_minutes': 15,
                'min_hours_full_day': 7.00,
                'min_hours_half_day': 3.50
            }
        )

    # Initialize summary fields
    check_in = None
    check_out = None
    working_hours = 0.00
    late_minutes = 0
    early_exit_minutes = 0
    overtime_minutes = 0
    status = 'ABSENT'
    remarks = ""

    # Check for approved leaves
    leave = LeaveRequest.objects.filter(
        employee=employee,
        start_date__lte=date,
        end_date__gte=date,
        status='APPROVED'
    ).first()

    # Check for public holidays
    holiday = Holiday.objects.filter(date=date).first()

    if not logs.exists():
        # No punches recorded
        if leave:
            status = 'ON_LEAVE'
            remarks = f"On Leave: {leave.leave_type.name}"
        elif holiday:
            status = 'HOLIDAY'
            remarks = f"Public Holiday: {holiday.name}"
        else:
            status = 'ABSENT'
            remarks = "No biometric log recorded."
            
        # Update or create summary
        summary, _ = AttendanceSummary.objects.update_or_create(
            employee=employee,
            date=date,
            defaults={
                'check_in': None,
                'check_out': None,
                'working_hours': 0.00,
                'late_minutes': 0,
                'early_exit_minutes': 0,
                'overtime_minutes': 0,
                'status': status,
                'remarks': remarks
            }
        )
        return summary

    # 1. Filter out duplicate/accidental punches within 5 minutes of each other
    sorted_logs = list(logs.order_by('timestamp'))
    filtered_logs = []
    for log in sorted_logs:
        if not filtered_logs:
            filtered_logs.append(log)
        else:
            time_diff = log.timestamp - filtered_logs[-1].timestamp
            if time_diff.total_seconds() > 300:  # 5 minutes
                filtered_logs.append(log)

    # 2. First punch of the day is check_in, last punch of the day is check_out
    check_in = filtered_logs[0].timestamp if filtered_logs else None
    check_out = filtered_logs[-1].timestamp if len(filtered_logs) > 1 else None

    # Working hours calculation by pairing up sequential punches (In-Out, In-Out...)
    total_worked_seconds = 0
    remarks = ""
    if len(filtered_logs) > 1:
        # Pair them up
        i = 0
        while i < len(filtered_logs) - 1:
            in_time = filtered_logs[i].timestamp
            out_time = filtered_logs[i+1].timestamp
            total_worked_seconds += (out_time - in_time).total_seconds()
            i += 2  # Move to next pair
            
        working_hours = round(total_worked_seconds / 3600.0, 2)
        if len(filtered_logs) % 2 != 0:
            remarks = "Odd number of punches. Last check-out missing or unmatched."
    else:
        working_hours = 0.00
        remarks = "Single punch recorded. Checkout missing."

    # Compare check_in time with shift.start_time
    late_minutes = 0
    if check_in:
        check_in_local = timezone.localtime(check_in)
        shift_start_time = datetime.datetime.combine(date, shift.start_time)
        shift_start_dt = timezone.make_aware(shift_start_time, local_tz)

        if check_in_local > shift_start_dt:
            diff_sec = (check_in_local - shift_start_dt).total_seconds()
            late_min = int(diff_sec // 60)
            if late_min > shift.grace_period_minutes:
                late_minutes = late_min

    # Compare check_out time with shift.end_time
    early_exit_minutes = 0
    overtime_minutes = 0
    if check_out:
        check_out_local = timezone.localtime(check_out)
        shift_end_time = datetime.datetime.combine(date, shift.end_time)
        shift_end_dt = timezone.make_aware(shift_end_time, local_tz)

        if check_out_local < shift_end_dt:
            diff_sec = (shift_end_dt - check_out_local).total_seconds()
            early_exit_min = int(diff_sec // 60)
            if early_exit_min > shift.early_exit_limit_minutes:
                early_exit_minutes = early_exit_min
        elif check_out_local > shift_end_dt:
            # Overtime
            diff_sec = (check_out_local - shift_end_dt).total_seconds()
            overtime_minutes = int(diff_sec // 60)

    # Determine status based on hours worked and late limits
    if working_hours == 0.00:
        status = 'ABSENT'
    elif late_minutes >= shift.half_day_limit_minutes:
        status = 'HALF_DAY'
        remarks = f"Half day: Arrived late by {late_minutes} minutes."
    elif working_hours >= float(shift.min_hours_full_day):
        status = 'PRESENT'
    elif working_hours >= float(shift.min_hours_half_day):
        status = 'HALF_DAY'
        remarks = (remarks + " " if remarks else "") + f"Half day: Worked {working_hours} hours."
    else:
        status = 'ABSENT'
        remarks = (remarks + " " if remarks else "") + f"Absent: Worked only {working_hours} hours."

    # Update or create summary
    summary, _ = AttendanceSummary.objects.update_or_create(
        employee=employee,
        date=date,
        defaults={
            'check_in': check_in,
            'check_out': check_out,
            'working_hours': working_hours,
            'late_minutes': late_minutes,
            'early_exit_minutes': early_exit_minutes,
            'overtime_minutes': overtime_minutes,
            'status': status,
            'remarks': remarks
        }
    )
    return summary
