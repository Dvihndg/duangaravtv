import re
import html
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from backend.app.models import CustomerRequestStatus

class CustomerRequestCreate(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=100, description="Họ và tên khách hàng")
    phone: str = Field(..., max_length=20, description="Số điện thoại liên hệ")
    email: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    
    licensePlate: str = Field(..., min_length=3, max_length=20, description="Biển số xe")
    vehicleBrand: str = Field(..., min_length=1, max_length=50, description="Hãng xe")
    vehicleModel: str = Field(..., min_length=1, max_length=50, description="Model xe")
    manufactureYear: Optional[int] = Field(default=2022, description="Năm sản xuất")
    currentMileage: Optional[int] = Field(default=0, description="Số km hiện tại")
    
    serviceType: str = Field(..., min_length=1, max_length=100, description="Loại dịch vụ yêu cầu")
    description: Optional[str] = Field(default=None, max_length=2000, description="Mô tả triệu chứng / sự cố")
    preferredDate: Optional[str] = Field(default=None, max_length=30)
    preferredTime: Optional[str] = Field(default=None, max_length=30)
    note: Optional[str] = Field(default=None, max_length=1000)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r'[\s\-\.]', '', v or '')
        if not re.match(r'^(0|\+84)[0-9]{9,10}$', cleaned):
            raise ValueError('Số điện thoại không hợp lệ (phải từ 10-11 chữ số)')
        return cleaned

    @field_validator('licensePlate')
    @classmethod
    def validate_license_plate(cls, v: str) -> str:
        cleaned = (v or '').strip().upper()
        if len(cleaned) < 4:
            raise ValueError('Biển số xe phải từ 4 ký tự trở lên')
        return cleaned

    @field_validator('fullName', 'serviceType', 'vehicleBrand', 'vehicleModel', 'description', 'note', 'address')
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Sanitize HTML tags to prevent XSS attacks
        sanitized = html.escape(v.strip())
        return sanitized


class CustomerRequestUpdateStatus(BaseModel):
    status: CustomerRequestStatus


class CustomerRequestAssign(BaseModel):
    assigned_employee_id: Optional[int] = None


class CustomerRequestAddNote(BaseModel):
    admin_note: str = Field(..., min_length=1, max_length=1000)


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
    appointmentId: Optional[int] = None
    source: Optional[str] = "CUSTOMER_PORTAL"
    
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)
