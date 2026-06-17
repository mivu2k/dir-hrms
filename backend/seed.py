import os
import django
import datetime
from django.utils import timezone

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from django.contrib.auth.models import User
from employees.models import Company, Department, Designation, Employee
from attendance.models import Shift, Holiday
from devices.models import Device
from leave.models import LeaveType, LeaveAllocation
from payroll.models import SalaryStructure

def seed_db():
    print("Starting database seeding...")
    
    # 1. Create Company
    company, created = Company.objects.get_or_create(
        code="AGC",
        defaults={
            "name": "Antigravity Corp",
            "address": "12A Architect Boulevard, Tech Zone",
            "email": "contact@antigravity.corp",
            "phone": "+92511234567",
            "tax_number": "TAX-987654-Z"
        }
    )
    if created:
        print("Created Company: Antigravity Corp")
        
    # 2. Create Departments
    dept_hr, _ = Department.objects.get_or_create(company=company, code="HRD", defaults={"name": "Human Resources"})
    dept_it, _ = Department.objects.get_or_create(company=company, code="ITD", defaults={"name": "Information Technology"})
    dept_fin, _ = Department.objects.get_or_create(company=company, code="FIN", defaults={"name": "Finance"})
    print("Created Departments: HR, IT, Finance")
    
    # 3. Create Designations
    desg_hrm, _ = Designation.objects.get_or_create(department=dept_hr, code="HRM", defaults={"name": "HR Manager"})
    desg_sa, _ = Designation.objects.get_or_create(department=dept_it, code="SA", defaults={"name": "Software Architect"})
    desg_dev, _ = Designation.objects.get_or_create(department=dept_it, code="SE", defaults={"name": "Software Engineer"})
    desg_acc, _ = Designation.objects.get_or_create(department=dept_fin, code="ACC", defaults={"name": "Senior Accountant"})
    print("Created Designations: HR Manager, Software Architect, Software Engineer, Senior Accountant")
    
    # 4. Create Shift
    morning_shift, _ = Shift.objects.get_or_create(
        name="Morning Shift",
        defaults={
            "start_time": datetime.time(9, 0),
            "end_time": datetime.time(17, 0),
            "grace_period_minutes": 15,
            "half_day_limit_minutes": 120,
            "early_exit_limit_minutes": 15,
            "min_hours_full_day": 7.00,
            "min_hours_half_day": 3.50,
            "is_active": True
        }
    )
    print("Created Shift: Morning Shift (09:00 - 17:00)")

    # 5. Create Leave Types
    leaves = [
        {"name": "Annual Leave", "code": "AL", "days": 15, "carry": True},
        {"name": "Casual Leave", "code": "CL", "days": 10, "carry": False},
        {"name": "Sick Leave", "code": "SL", "days": 8, "carry": False},
    ]
    leave_types = []
    for l in leaves:
        lt, _ = LeaveType.objects.get_or_create(
            code=l["code"],
            defaults={
                "name": l["name"],
                "days_per_year": l["days"],
                "carry_forward": l["carry"],
                "is_paid": True
            }
        )
        leave_types.append(lt)
    print("Created Leave Types: Annual, Casual, Sick")

    # 6. Create Device
    device, _ = Device.objects.get_or_create(
        ip_address="192.168.1.201",
        port=4370,
        defaults={
            "name": "Reception uFace800",
            "location": "Reception Main Hall",
            "is_simulated": True,
            "is_active": True,
            "connection_status": "ONLINE"
        }
    )
    print("Created Simulated ZKTeco Device at 192.168.1.201:4370")

    # 7. Create Public Holiday
    Holiday.objects.get_or_create(
        date=datetime.date(2026, 8, 14),
        defaults={"name": "Independence Day", "description": "National Independence Day of Pakistan"}
    )
    Holiday.objects.get_or_create(
        date=datetime.date(2026, 12, 25),
        defaults={"name": "Quaid-e-Azam Day", "description": "Birthday of Quaid-e-Azam Muhammad Ali Jinnah / Christmas"}
    )
    print("Created Public Holidays: Independence Day, Quaid-e-Azam Day")

    # 8. Create Users and Employee Profiles
    users_data = [
        {
            "username": "admin",
            "first": "Antigravity",
            "last": "Admin",
            "email": "admin@antigravity.corp",
            "role": "SUPER_ADMIN",
            "emp_id": "EMP-001",
            "bio_id": "1",
            "desg": desg_sa,
            "dept": dept_it,
            "salary": 180000.00
        },
        {
            "username": "hr_manager",
            "first": "Sarah",
            "last": "Khan",
            "email": "sarah.hr@antigravity.corp",
            "role": "HR_MANAGER",
            "emp_id": "EMP-002",
            "bio_id": "2",
            "desg": desg_hrm,
            "dept": dept_hr,
            "salary": 120000.00
        },
        {
            "username": "accountant",
            "first": "Kamran",
            "last": "Ali",
            "email": "kamran.fin@antigravity.corp",
            "role": "ACCOUNTANT",
            "emp_id": "EMP-003",
            "bio_id": "3",
            "desg": desg_acc,
            "dept": dept_fin,
            "salary": 95000.00
        },
        {
            "username": "john_dev",
            "first": "John",
            "last": "Doe",
            "email": "john.doe@antigravity.corp",
            "role": "EMPLOYEE",
            "emp_id": "EMP-004",
            "bio_id": "4",
            "desg": desg_dev,
            "dept": dept_it,
            "salary": 85000.00
        },
        {
            "username": "ali_dev",
            "first": "Ali",
            "last": "Ahmed",
            "email": "ali.ahmed@antigravity.corp",
            "role": "EMPLOYEE",
            "emp_id": "EMP-005",
            "bio_id": "5",
            "desg": desg_dev,
            "dept": dept_it,
            "salary": 75000.00
        }
    ]

    for ud in users_data:
        # Create standard Auth User
        user, created = User.objects.get_or_create(
            username=ud["username"],
            defaults={
                "email": ud["email"],
                "first_name": ud["first"],
                "last_name": ud["last"],
                "is_staff": ud["role"] in ["SUPER_ADMIN", "HR_MANAGER"],
                "is_superuser": ud["role"] == "SUPER_ADMIN"
            }
        )
        if created:
            user.set_password("admin123")
            user.save()
            print(f"Created Auth User: {ud['username']} (password: admin123)")

        # Create Employee profile
        emp, emp_created = Employee.objects.get_or_create(
            employee_id=ud["emp_id"],
            defaults={
                "user": user,
                "bio_device_user_id": ud["bio_id"],
                "first_name": ud["first"],
                "last_name": ud["last"],
                "email": ud["email"],
                "role": ud["role"],
                "status": "ACTIVE",
                "department": ud["dept"],
                "designation": ud["desg"],
                "shift": morning_shift,
                "joining_date": datetime.date(2025, 1, 1),
                "cnic": f"42101-123456{ud['bio_id']}-9",
                "phone": f"+92300123456{ud['bio_id']}"
            }
        )
        if emp_created:
            print(f"Created Employee Profile: {ud['first']} {ud['last']}")

        # Create Salary Structure
        SalaryStructure.objects.get_or_create(
            employee=emp,
            defaults={
                "basic_salary": ud["salary"],
                "allowances": ud["salary"] * 0.15,  # 15% allowance
                "eobi_contribution": 1000.00,
                "provident_fund": ud["salary"] * 0.05,  # 5% fund
                "tax_percentage": 5.0  # 5% flat tax rate
            }
        )

        # Allocate Leaves for year 2026
        for lt in leave_types:
            LeaveAllocation.objects.get_or_create(
                employee=emp,
                leave_type=lt,
                year=2026,
                defaults={
                    "allocated_days": lt.days_per_year,
                    "used_days": 0.00
                }
            )

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_db()
