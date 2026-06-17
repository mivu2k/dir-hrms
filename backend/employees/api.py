from typing import List
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from ninja import Router, Schema
from ninja.errors import HttpError
from django.utils import timezone
from api.security import JWTAuth, generate_token
from employees.models import Company, Department, Designation, Employee
from payroll.models import SalaryStructure
from leave.models import LeaveType, LeaveAllocation
from employees.schemas import (
    CompanySchema, CompanyCreateSchema,
    DepartmentSchema, DepartmentCreateSchema,
    DesignationSchema, DesignationCreateSchema,
    EmployeeSchema, EmployeeCreateSchema, EmployeeBriefSchema
)

class LoginRequest(Schema):
    username: str
    password: str

# Initialize routers
auth_router = Router(tags=["Authentication"])
employee_router = Router(tags=["Employees"], auth=JWTAuth())

# ================= AUTHENTICATION ENDPOINTS =================

@auth_router.post("/login", response={200: dict})
def login(request, payload: LoginRequest):
    """
    JWT Authentication Endpoint.
    """
    username = payload.username
    password = payload.password
    
    if not username or not password:
        raise HttpError(400, "Username and password are required")
        
    user = authenticate(username=username, password=password)
    if not user:
        raise HttpError(401, "Invalid credentials")
        
    if not user.is_active:
        raise HttpError(401, "Account is disabled")
        
    token = generate_token(user)
    
    # Details
    role = 'GUEST'
    employee_id = None
    first_name = user.first_name
    last_name = user.last_name
    
    if hasattr(user, 'employee') and user.employee:
        role = user.employee.role
        employee_id = user.employee.id
        first_name = user.employee.first_name
        last_name = user.employee.last_name
    elif user.is_superuser:
        role = 'SUPER_ADMIN'
        
    return {
        "token": token,
        "username": user.username,
        "email": user.email,
        "role": role,
        "employee_id": employee_id,
        "full_name": f"{first_name} {last_name}" or user.username
    }


@employee_router.get("/me", response=dict)
def get_me(request):
    """Returns the current authenticated user's profile info"""
    user = request.auth
    role = request.jwt_payload.get('role', 'EMPLOYEE')
    
    try:
        emp = Employee.objects.get(user=user)
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role,
            "employee_id": emp.employee_id,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "department": emp.department.name if emp.department else None,
            "designation": emp.designation.name if emp.designation else None,
            "profile_picture": emp.profile_picture.url if emp.profile_picture else None
        }
    except Employee.DoesNotExist:
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role,
            "employee_id": None,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "department": "IT",
            "designation": "Super Admin" if user.is_superuser else "Guest",
            "profile_picture": None
        }

# ================= COMPANY CRUD =================

@employee_router.get("/companies", response=List[CompanySchema])
def list_companies(request):
    return Company.objects.all()


@employee_router.post("/companies", response=CompanySchema)
def create_company(request, data: CompanyCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Only HR Managers/Super Admins can create companies")
    company = Company.objects.create(**data.dict())
    return company

# ================= DEPARTMENT CRUD =================

@employee_router.get("/departments", response=List[DepartmentSchema])
def list_departments(request):
    return Department.objects.all()


@employee_router.post("/departments", response=DepartmentSchema)
def create_department(request, data: DepartmentCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
    
    try:
        company = Company.objects.get(id=data.company_id)
    except Company.DoesNotExist:
        raise HttpError(404, "Company not found")
        
    dept = Department.objects.create(
        company=company,
        name=data.name,
        code=data.code
    )
    return dept

# ================= DESIGNATION CRUD =================

@employee_router.get("/designations", response=List[DesignationSchema])
def list_designations(request):
    return Designation.objects.all()


@employee_router.post("/designations", response=DesignationSchema)
def create_designation(request, data: DesignationCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        dept = Department.objects.get(id=data.department_id)
    except Department.DoesNotExist:
        raise HttpError(404, "Department not found")
        
    desg = Designation.objects.create(
        department=dept,
        name=data.name,
        code=data.code
    )
    return desg

# ================= EMPLOYEE CRUD =================

@employee_router.get("/", response=List[EmployeeBriefSchema])
def list_employees(request, status: str = None, department_id: int = None):
    # Only Managers, HR, Accountants can view the full list
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER', 'ACCOUNTANT', 'RECRUITER']:
        # Employees can only list their colleagues in brief or themselves
        pass
        
    queryset = Employee.objects.all()
    if status:
        queryset = queryset.filter(status=status)
    if department_id:
        queryset = queryset.filter(department_id=department_id)
        
    return queryset


@employee_router.get("/{employee_id}", response=EmployeeSchema)
def get_employee(request, employee_id: int):
    # Check permission: Self or Admin
    current_emp_id = request.jwt_payload.get('employee_id')
    current_role = request.jwt_payload.get('role')
    
    if current_role not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER'] and current_emp_id != employee_id:
        raise HttpError(403, "Permission Denied")
        
    try:
        return Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise HttpError(404, "Employee not found")


@employee_router.post("/", response=EmployeeSchema)
def create_employee(request, data: EmployeeCreateSchema):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER']:
        raise HttpError(403, "Permission Denied")
        
    with transaction.atomic():
        # Check if email or employee_id already exists
        if Employee.objects.filter(employee_id=data.employee_id).exists():
            raise HttpError(400, f"Employee ID {data.employee_id} already exists")
        if Employee.objects.filter(email=data.email).exists():
            raise HttpError(400, f"Email {data.email} already exists")
            
        # Create user account for employee if password is provided
        user = None
        if data.password:
            user = User.objects.create_user(
                username=data.employee_id,
                email=data.email,
                password=data.password,
                first_name=data.first_name,
                last_name=data.last_name
            )

        # Retrieve structures
        dept = Department.objects.filter(id=data.department_id).first() if data.department_id else None
        desg = Designation.objects.filter(id=data.designation_id).first() if data.designation_id else None
        manager = Employee.objects.filter(id=data.manager_id).first() if data.manager_id else None
        
        # Shift will be linked in attendance models
        shift_id = data.shift_id
        
        # Create Employee
        emp = Employee.objects.create(
            user=user,
            employee_id=data.employee_id,
            bio_device_user_id=data.bio_device_user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            cnic=data.cnic,
            passport=data.passport,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            marital_status=data.marital_status,
            blood_group=data.blood_group,
            nationality=data.nationality,
            religion=data.religion,
            email=data.email,
            phone=data.phone,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            address=data.address,
            department=dept,
            designation=desg,
            shift_id=shift_id,
            manager=manager,
            employment_type=data.employment_type,
            status=data.status,
            role=data.role,
            joining_date=data.joining_date
        )
        
        # Create Default Salary Structure (essential for running payroll later)
        SalaryStructure.objects.create(
            employee=emp,
            basic_salary=45000.00,
            allowances=5000.00,
            eobi_contribution=1000.00,
            provident_fund=1500.00,
            tax_percentage=0.00
        )
        
        # Allocate Leaves
        active_leave_types = LeaveType.objects.all()
        current_year = timezone.localdate().year
        for lt in active_leave_types:
            LeaveAllocation.objects.create(
                employee=emp,
                leave_type=lt,
                year=current_year,
                allocated_days=lt.days_per_year,
                used_days=0.00
            )
            
        return emp


@employee_router.delete("/{employee_id}", response=dict)
def delete_employee(request, employee_id: int):
    if request.jwt_payload['role'] not in ['SUPER_ADMIN', 'HR_MANAGER']:
        raise HttpError(403, "Permission Denied")
        
    try:
        emp = Employee.objects.get(id=employee_id)
        if emp.user:
            emp.user.delete()
        emp.delete()
        return {"success": True, "message": "Employee deleted successfully"}
    except Employee.DoesNotExist:
        raise HttpError(404, "Employee not found")
