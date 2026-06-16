from pydantic import BaseModel
from typing import Optional, List
from datetime import time, date, datetime
from employees.schemas import EmployeeBriefSchema

class ShiftSchema(BaseModel):
    id: int
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int
    half_day_limit_minutes: int
    early_exit_limit_minutes: int
    min_hours_full_day: float
    min_hours_half_day: float
    is_active: bool

    class Config:
        from_attributes = True


class ShiftCreateSchema(BaseModel):
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: Optional[int] = 15
    half_day_limit_minutes: Optional[int] = 120
    early_exit_limit_minutes: Optional[int] = 15
    min_hours_full_day: Optional[float] = 8.00
    min_hours_half_day: Optional[float] = 4.00
    is_active: Optional[bool] = True


class AttendanceLogSchema(BaseModel):
    id: int
    employee: EmployeeBriefSchema
    device_id: Optional[int] = None
    timestamp: datetime
    punch_type: str
    verification_mode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


class AttendanceLogCreateSchema(BaseModel):
    # Used for manual Web punches or GPS punches
    punch_type: str  # CHECK_IN, CHECK_OUT
    verification_mode: str  # WEB, GPS
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AttendanceSummarySchema(BaseModel):
    id: int
    employee: EmployeeBriefSchema
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    working_hours: float
    late_minutes: int
    early_exit_minutes: int
    overtime_minutes: int
    status: str
    is_approved: bool
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceCorrectionRequestSchema(BaseModel):
    id: int
    employee: EmployeeBriefSchema
    date: date
    requested_check_in: Optional[time] = None
    requested_check_out: Optional[time] = None
    reason: str
    status: str
    approved_by: Optional[EmployeeBriefSchema] = None
    comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceCorrectionCreateSchema(BaseModel):
    date: date
    requested_check_in: Optional[time] = None
    requested_check_out: Optional[time] = None
    reason: str


class HolidaySchema(BaseModel):
    id: int
    name: str
    date: date
    description: Optional[str] = None

    class Config:
        from_attributes = True
