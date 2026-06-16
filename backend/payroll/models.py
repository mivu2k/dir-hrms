from django.db import models
from employees.models import Employee

class SalaryStructure(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    eobi_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salary for {self.employee.employee_id} ({self.basic_salary})"


class Payroll(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
    ]

    month = models.IntegerField()  # 1 to 12
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    generated_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')

    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Payroll {self.year}-{self.month:02d} ({self.status})"


class Payslip(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PAID', 'Paid'),
    ]

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Deductions
    late_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    eobi_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    provident_fund_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('payroll', 'employee')

    def __str__(self):
        return f"Payslip {self.employee.employee_id} - {self.payroll.year}-{self.payroll.month:02d} ({self.net_salary})"
