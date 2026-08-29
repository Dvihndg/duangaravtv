from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import re

from backend.app.models import CustomerRequestStatus

class CustomerRequestCreate(BaseModel):
    fullName: str = Field(..., min_length=2, description="Họ và tên khách hàng")
    phone: str = Field(..., description="Số điện thoại liên hệ")
    email: Optional[str] = None
    address: Optional[str] = None
    
    licensePlate: str = Field(..., min_length=3, description="Biển số xe")
    vehicleBrand: str = Field(..., min_length=1, description="Hãng xe")
    vehicleModel: str = Field(..., min_length=1, description="Model xe")
    manufactureYear: Optional[int] = Field(default=2022, description="Năm sản xuất")
    currentMileage: Optional[int] = Field(default=0, description="Số km hiện tại")
    
    serviceType: str = Field(..., description="Loại dịch vụ yêu cầu")
    description: Optional[str] = None
    preferredDate: Optional[str] = None
    preferredTime: Optional[str] = None
    note: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        cleaned = re.sub(r'[\s\-\.]', '', v)
        if not re.match(r'^(0|\+84)[0-9]{9,10}$', cleaned):
            raise ValueError('Số điện thoại không hợp lệ (phải từ 10-11 chữ số)')
        return cleaned

    @validator('licensePlate')
    def validate_license_plate(cls, v):
        cleaned = v.strip().upper()
        if len(cleaned) < 4:
            raise ValueError('Biển số xe phải từ 4 ký tự trở lên')
        return cleaned


class CustomerRequestUpdateStatus(BaseModel):
    status: CustomerRequestStatus


class CustomerRequestAssign(BaseModel):
    assigned_employee_id: Optional[int] = None


class CustomerRequestAddNote(BaseModel):
    admin_note: str = Field(..., min_length=1)


class CustomerRequestResponse(BaseModel):
    id: int
    requestCode: str
    fullName: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    
    licensePlate: str
    vehicleBrand: str
    vehicleModel: str
    manufactureYear: Optional[int] = None
    currentMileage: Optional[int] = 0
    
    serviceType: str
    description: Optional[str] = None
    preferredDate: Optional[str] = None
    preferredTime: Optional[str] = None
    note: Optional[str] = None
    
    status: CustomerRequestStatus
    adminNote: Optional[str] = None
    assignedEmployeeId: Optional[int] = None
    assignedEmployeeName: Optional[str] = None
    
    customerId: Optional[int] = None
    vehicleId: Optional[int] = None
    
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
