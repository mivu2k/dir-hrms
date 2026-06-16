from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

class CompanySchema(BaseModel):
    id: int
    name: str
    code: str
    logo: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_number: Optional[str] = None

    class Config:
        from_attributes = True


class CompanyCreateSchema(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_number: Optional[str] = None


class DepartmentSchema(BaseModel):
    id: int
    company_id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class DepartmentCreateSchema(BaseModel):
    company_id: int
    name: str
    code: str


class DesignationSchema(BaseModel):
    id: int
    department_id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class DesignationCreateSchema(BaseModel):
    department_id: int
    name: str
    code: str


class EmployeeBriefSchema(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    email: str
    role: str
    status: str

    class Config:
        from_attributes = True


class EmployeeSchema(BaseModel):
    id: int
    employee_id: str
    bio_device_user_id: Optional[str] = None
    first_name: str
    last_name: str
    cnic: Optional[str] = None
    passport: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: str
    marital_status: str
    blood_group: Optional[str] = None
    nationality: str
    religion: Optional[str] = None
    email: str
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    
    department: Optional[DepartmentSchema] = None
    designation: Optional[DesignationSchema] = None
    shift_id: Optional[int] = None
    manager_id: Optional[int] = None
    
    employment_type: str
    status: str
    role: str
    
    joining_date: date
    confirmation_date: Optional[date] = None
    resignation_date: Optional[date] = None
    termination_date: Optional[date] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeCreateSchema(BaseModel):
    employee_id: str
    bio_device_user_id: Optional[str] = None
    first_name: str
    last_name: str
    cnic: Optional[str] = None
    passport: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = "MALE"
    marital_status: Optional[str] = "SINGLE"
    blood_group: Optional[str] = None
    nationality: Optional[str] = "Pakistani"
    religion: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None
    
    department_id: Optional[int] = None
    designation_id: Optional[int] = None
    shift_id: Optional[int] = None
    manager_id: Optional[int] = None
    
    employment_type: Optional[str] = "REGULAR"
    status: Optional[str] = "ACTIVE"
    role: Optional[str] = "EMPLOYEE"
    
    joining_date: date
    password: Optional[str] = None  # To create linked Django auth User
