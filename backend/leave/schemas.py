from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from employees.schemas import EmployeeBriefSchema

class LeaveTypeSchema(BaseModel):
    id: int
    name: str
    code: str
    days_per_year: int
    is_paid: bool
    carry_forward: bool

    class Config:
        from_attributes = True


class LeaveAllocationSchema(BaseModel):
    id: int
    employee: EmployeeBriefSchema
    leave_type: LeaveTypeSchema
    year: int
    allocated_days: float
    used_days: float

    class Config:
        from_attributes = True


class LeaveRequestSchema(BaseModel):
    id: int
    employee: EmployeeBriefSchema
    leave_type: LeaveTypeSchema
    start_date: date
    end_date: date
    reason: str
    status: str
    manager_approved_by: Optional[EmployeeBriefSchema] = None
    hr_approved_by: Optional[EmployeeBriefSchema] = None
    comments: Optional[str] = None
    created_at: datetime
    total_days: int

    class Config:
        from_attributes = True


class LeaveRequestCreateSchema(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str
