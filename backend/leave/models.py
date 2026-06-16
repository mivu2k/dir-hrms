from django.db import models
from employees.models import Employee

class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    days_per_year = models.IntegerField(default=10)
    is_paid = models.BooleanField(default=True)
    carry_forward = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeaveAllocation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_allocations')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='allocations')
    year = models.IntegerField()
    allocated_days = models.DecimalField(max_digits=5, decimal_places=2)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.code} for {self.year} (Allocated: {self.allocated_days}, Used: {self.used_days})"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('MANAGER_APPROVED', 'Manager Approved'),
        ('APPROVED', 'Approved (HR)'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    manager_approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_approved_leaves')
    hr_approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_approved_leaves')
    comments = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.code} ({self.start_date} to {self.end_date}) - {self.status}"
