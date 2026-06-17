from django.db import models
from employees.models import Employee
from devices.models import Device

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    grace_period_minutes = models.IntegerField(default=15)
    half_day_limit_minutes = models.IntegerField(default=120)
    early_exit_limit_minutes = models.IntegerField(default=15)
    
    min_hours_full_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)
    min_hours_half_day = models.DecimalField(max_digits=4, decimal_places=2, default=4.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class AttendanceLog(models.Model):
    PUNCH_CHOICES = [
        ('CHECK_IN', 'Check In'),
        ('CHECK_OUT', 'Check Out'),
        ('BREAK_IN', 'Break In'),
        ('BREAK_OUT', 'Break Out'),
        ('UNKNOWN', 'Unknown'),
    ]

    VERIFICATION_CHOICES = [
        ('FINGER', 'Fingerprint'),
        ('FACE', 'Face Recognition'),
        ('RFID', 'RFID Card'),
        ('MANUAL', 'Manual Log'),
        ('WEB', 'Web Attendance'),
        ('GPS', 'GPS Mobile App'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_logs')
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_logs')
    timestamp = models.DateTimeField()
    punch_type = models.CharField(max_length=20, choices=PUNCH_CHOICES, default='UNKNOWN')
    verification_mode = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='FINGER')
    
    # Optional GPS Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'timestamp')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({self.punch_type})"


class AttendanceSummary(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Leave'),
        ('HOLIDAY', 'Holiday'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_summaries')
    date = models.DateField()
    
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_minutes = models.IntegerField(default=0)
    early_exit_minutes = models.IntegerField(default=0)
    overtime_minutes = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABSENT')
    is_approved = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} ({self.status})"


class AttendanceCorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='correction_requests')
    date = models.DateField()
    
    requested_check_in = models.TimeField(null=True, blank=True)
    requested_check_out = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_corrections')
    comments = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.employee_id} - Correction for {self.date} ({self.status})"


class Holiday(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField(unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"
