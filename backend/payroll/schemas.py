from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from employees.schemas import EmployeeBriefSchema

class SalaryStructureSchema(BaseModel):
    id: int
    employee: EmployeeBriefSchema
    basic_salary: float
    allowances: float
    eobi_contribution: float
    provident_fund: float
    tax_percentage: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalaryStructureUpdateSchema(BaseModel):
    basic_salary: float
    allowances: Optional[float] = 0.00
    eobi_contribution: Optional[float] = 0.00
    provident_fund: Optional[float] = 0.00
    tax_percentage: Optional[float] = 0.00


class PayrollSchema(BaseModel):
    id: int
    month: int
    year: int
    status: str
    generated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[EmployeeBriefSchema] = None

    class Config:
        from_attributes = True


class PayslipSchema(BaseModel):
    id: int
    payroll: PayrollSchema
    employee: EmployeeBriefSchema
    basic_salary: float
    allowances: float
    overtime_amount: float
    bonus: float
    late_deduction: float
    leave_deduction: float
    tax_deduction: float
    eobi_deduction: float
    provident_fund_deduction: float
    net_salary: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
