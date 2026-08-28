from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models import UserRole, AppointmentStatus, RepairOrderStatus, InvoiceStatus, PaymentMethod, RepairOrderItemType

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Customer & Vehicle Schemas
class VehicleBase(BaseModel):
    license_plate: str
    brand: str
    model: str
    year: Optional[int] = None
    color: Optional[str] = None
    vin_number: Optional[str] = None
    current_mileage: Optional[int] = 0

class VehicleCreate(VehicleBase):
    customer_id: Optional[int] = None # Can be specified or created together

class VehicleOut(VehicleBase):
    id: int
    customer_id: int
    
    model_config = ConfigDict(from_attributes=True)

class CustomerBase(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    vehicles: List[VehicleOut] = []

    model_config = ConfigDict(from_attributes=True)

# Appointment Schemas
class AppointmentCreate(BaseModel):
    vehicle_id: int
    appointment_date: datetime
    notes: Optional[str] = None
    assigned_technician_id: Optional[int] = None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    assigned_technician_id: Optional[int] = None

class AppointmentOut(BaseModel):
    id: int
    vehicle_id: int
    appointment_date: datetime
    notes: Optional[str] = None
    status: AppointmentStatus
    assigned_technician_id: Optional[int] = None
    created_at: datetime
    vehicle: Optional[VehicleOut] = None

    model_config = ConfigDict(from_attributes=True)

# Catalog Schemas (Service & Part)
class ServiceBase(BaseModel):
    code: str
    name: str
    category: Optional[str] = "Bảo dưỡng"
    description: Optional[str] = None
    labor_cost: float = 0.0
    estimated_hours: float = 1.0

class ServiceCreate(ServiceBase):
    pass

class ServiceOut(ServiceBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class PartBase(BaseModel):
    code: str
    name: str
    brand: Optional[str] = None
    unit_price: float = 0.0
    cost_price: float = 0.0
    stock_quantity: int = 0
    min_stock_alert: int = 5

class PartCreate(PartBase):
    pass

class PartOut(PartBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Repair Order Item Schemas
class RepairOrderItemCreate(BaseModel):
    item_type: RepairOrderItemType
    service_id: Optional[int] = None
    part_id: Optional[int] = None
    name: str
    quantity: float = 1.0
    unit_price: float = 0.0
    labor_cost: float = 0.0
    notes: Optional[str] = None

class RepairOrderItemOut(RepairOrderItemCreate):
    id: int
    repair_order_id: int
    total_price: float

    model_config = ConfigDict(from_attributes=True)

# Repair Order Schemas
class RepairOrderCreate(BaseModel):
    vehicle_id: int
    mileage_at_reception: int = 0
    initial_symptoms: Optional[str] = None
    technician_id: Optional[int] = None

class RepairOrderUpdate(BaseModel):
    mileage_at_reception: Optional[int] = None
    initial_symptoms: Optional[str] = None
    technical_diagnosis: Optional[str] = None
    status: Optional[RepairOrderStatus] = None
    technician_id: Optional[int] = None

class RepairOrderOut(BaseModel):
    id: int
    code: str
    vehicle_id: int
    technician_id: Optional[int] = None
    receptionist_id: Optional[int] = None
    mileage_at_reception: int
    initial_symptoms: Optional[str] = None
    technical_diagnosis: Optional[str] = None
    status: RepairOrderStatus
    estimated_cost: float
    final_cost: float
    ai_history_summary: Optional[str] = None
    ai_service_explanation: Optional[str] = None
    ai_draft_quotation_notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    vehicle: Optional[VehicleOut] = None
    items: List[RepairOrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)

# Invoice & Payment Schemas
class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    repair_order_id: int
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    status: InvoiceStatus
    issued_date: datetime
    due_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(BaseModel):
    invoice_id: int
    payment_method: PaymentMethod = PaymentMethod.CASH
    amount: float
    transaction_reference: Optional[str] = None

class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    payment_method: PaymentMethod
    amount: float
    transaction_reference: Optional[str] = None
    payment_date: datetime
    cashier_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# AI Schemas
class AIAssistantRequest(BaseModel):
    question: str
    repair_order_id: Optional[int] = None
    vehicle_id: Optional[int] = None

class AIHistorySummaryRequest(BaseModel):
    vehicle_id: int

class AIServiceExplainerRequest(BaseModel):
    repair_order_id: int

class AIDraftQuotationRequest(BaseModel):
    repair_order_id: int

class AIResponse(BaseModel):
    success: bool
    feature: str
    output: str
    model_used: str
    metadata: Optional[dict] = None

class AIEvaluationMetricsResponse(BaseModel):
    total_interactions: int
    top1_accuracy_percent: float
    parts_accuracy_percent: float
    price_variance_percent: float
    average_latency_ms: float
    total_token_count: int
    total_estimated_cost_usd: float
    status_summary: dict

class DemoScenarioResponse(BaseModel):
    scenario_id: int
    scenario_title: str
    scenario_description: str
    status: str
    symptoms: str
    diagnosis: str
    suggested_parts: List[dict]
    suggested_services: List[dict]
    estimated_total: float
    warnings: List[str]
    ai_raw_output: str


