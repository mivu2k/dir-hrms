from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    tax_number = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Designation(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Employee(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('DIVORCED', 'Divorced'),
        ('WIDOWED', 'Widowed'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('REGULAR', 'Regular'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
        ('PART_TIME', 'Part Time'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PROBATION', 'Probation'),
        ('SUSPENDED', 'Suspended'),
        ('RESIGNED', 'Resigned'),
        ('TERMINATED', 'Terminated'),
    ]

    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('HR_MANAGER', 'HR Manager'),
        ('HR_OFFICER', 'HR Officer'),
        ('DEPT_MANAGER', 'Department Manager'),
        ('TEAM_LEAD', 'Team Lead'),
        ('ACCOUNTANT', 'Accountant'),
        ('RECRUITER', 'Recruiter'),
        ('EMPLOYEE', 'Employee'),
        ('GUEST', 'Guest'),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee')
    employee_id = models.CharField(max_length=50, unique=True)
    bio_device_user_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    cnic = models.CharField(max_length=20, null=True, blank=True, unique=True, verbose_name="CNIC / National ID")
    passport = models.CharField(max_length=50, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='MALE')
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, default='SINGLE')
    blood_group = models.CharField(max_length=10, null=True, blank=True)
    nationality = models.CharField(max_length=100, default='Pakistani')
    religion = models.CharField(max_length=100, null=True, blank=True)
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=150, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    shift = models.ForeignKey('attendance.Shift', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_TYPE_CHOICES, default='REGULAR')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='ACTIVE')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='EMPLOYEE')
    
    joining_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"


class EmployeeDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('CNIC', 'CNIC / National ID'),
        ('PASSPORT', 'Passport'),
        ('CERTIFICATE', 'Educational Certificate'),
        ('EXPERIENCE', 'Experience Letter'),
        ('CONTRACT', 'Employment Contract'),
        ('OFFER_LETTER', 'Offer Letter'),
        ('MEDICAL', 'Medical Record'),
        ('NDA', 'Non-Disclosure Agreement'),
        ('OTHER', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='employee_documents/')
    version = models.IntegerField(default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.document_type} - {self.employee.employee_id} (v{self.version})"
