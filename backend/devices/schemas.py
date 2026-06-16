from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceSchema(BaseModel):
    id: int
    name: str
    ip_address: str
    port: int
    location: Optional[str] = None
    is_active: bool
    is_simulated: bool
    connection_status: str
    last_sync_time: Optional[datetime] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceCreateSchema(BaseModel):
    name: str
    ip_address: str
    port: Optional[int] = 4370
    location: Optional[str] = None
    is_active: Optional[bool] = True
    is_simulated: Optional[bool] = True


class DeviceLogSchema(BaseModel):
    id: int
    device_id: int
    event_type: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True
