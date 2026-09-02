from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base

class UserRole(str, enum.Enum):
    MANAGER = "manager"          # Quản lý
    RECEPTIONIST = "receptionist"# Lễ tân
    TECHNICIAN = "technician"    # Kỹ thuật viên
    CASHIER = "cashier"          # Thu ngân

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class RepairOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    RECEIVED = "received"        # Tiếp nhận
    INSPECTING = "inspecting"    # Đang chẩn đoán
    QUOTATION_PENDING = "quotation_pending" # Chờ báo giá
    WAITING_CUSTOMER_APPROVAL = "waiting_customer_approval" # Chờ khách duyệt
    APPROVED = "approved"        # Khách duyệt Báo giá / Phê duyệt
    IN_REPAIR = "in_repair"      # Đang sửa chữa
    WAITING_PARTS = "waiting_parts" # Chờ phụ tùng
    QUALITY_CHECK = "quality_check" # KCS nghiệm thu
    COMPLETED = "completed"      # Hoàn thành xuất xưởng
    FINISHED = "finished"        # Hoàn tất kỹ thuật
    INVOICED = "invoiced"        # Đã lập hóa đơn
    CANCELLED = "cancelled"      # Hủy bỏ

class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class InvoiceStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CARD = "card"
    OTHER = "other"

class CustomerRequestStatus(str, enum.Enum):
    PENDING = "Pending"
    CONTACTED = "Contacted"
    CONFIRMED = "Confirmed"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    CONVERTED = "Converted"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"

class InspectionCategory(str, enum.Enum):
    ENGINE = "ENGINE"
    TRANSMISSION = "TRANSMISSION"
    BRAKES = "BRAKES"
    SUSPENSION = "SUSPENSION"
    ELECTRICAL = "ELECTRICAL"
    AIR_CONDITIONING = "AIR_CONDITIONING"
    TIRES = "TIRES"
    BATTERY = "BATTERY"
    LIGHTS = "LIGHTS"
    BODY = "BODY"
    INTERIOR = "INTERIOR"
    OTHER = "OTHER"

class InspectionSeverity(str, enum.Enum):
    NORMAL = "NORMAL"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class InventoryTransactionType(str, enum.Enum):
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    ADJUSTMENT = "ADJUSTMENT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.RECEPTIONIST, nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(30), unique=True, index=True, nullable=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True) # Soft delete

    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, index=True, nullable=False) # Biển số xe
    brand = Column(String(50), nullable=False) # Hãng xe
    model = Column(String(50), nullable=False) # Dòng xe
    year = Column(Integer, nullable=True) # Năm sản xuất
    color = Column(String(30), nullable=True)
    vin_number = Column(String(50), index=True, nullable=True) # Số khung VIN
    engine_number = Column(String(50), nullable=True) # Số máy
    current_mileage = Column(Integer, default=0) # Số km hiện tại
    fuel_type = Column(String(20), default="GASOLINE")
    transmission = Column(String(20), default="AUTOMATIC")
    notes = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("Customer", back_populates="vehicles")
    appointments = relationship("Appointment", back_populates="vehicle")
    repair_orders = relationship("RepairOrder", back_populates="vehicle")
    receptions = relationship("VehicleReception", back_populates="vehicle")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_code = Column(String(30), unique=True, index=True, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)
    service_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    assigned_technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="appointments")
    technician = relationship("User", foreign_keys=[assigned_technician_id])

class VehicleReception(Base):
    __tablename__ = "vehicle_receptions"

    id = Column(Integer, primary_key=True, index=True)
    reception_code = Column(String(30), unique=True, index=True, nullable=False) # REC-2026-000001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    mileage = Column(Integer, nullable=False, default=0)
    fuel_level = Column(String(20), default="1/2")
    exterior_condition = Column(Text, nullable=True) # Vết xước, móp méo
    interior_condition = Column(Text, nullable=True) # Đồ đạc trên xe
    existing_damage = Column(Text, nullable=True)
    customer_complaint = Column(Text, nullable=False) # Khiếu nại / yêu cầu của khách
    requested_services = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    received_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer")
    vehicle = relationship("Vehicle", back_populates="receptions")
    received_by = relationship("User")
    appointment = relationship("Appointment")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False) # SER-001
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="Bảo dưỡng")
    description = Column(Text, nullable=True)
    labor_cost = Column(Float, default=0.0) # Chi phí công thợ
    estimated_hours = Column(Float, default=1.0)
    estimated_duration = Column(Integer, default=60) # Phút
    warranty_period = Column(String(50), default="6 tháng")
    is_active = Column(Boolean, default=True)

class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False) # PAR-001
    name = Column(String(150), nullable=False)
    brand = Column(String(50), nullable=True)
    category = Column(String(50), default="Phụ tùng thay thế")
    unit = Column(String(20), default="Cái")
    unit_price = Column(Float, default=0.0) # Giá bán
    cost_price = Column(Float, default=0.0) # Giá nhập
    stock_quantity = Column(Integer, default=0)
    min_stock_alert = Column(Integer, default=5)
    supplier = Column(String(100), nullable=True)
    location = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

# Alias for SparePart
SparePart = Part

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    transaction_type = Column(Enum(InventoryTransactionType), nullable=False) # IMPORT, EXPORT, ADJUSTMENT
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(50), nullable=True) # REPAIR_ORDER, PURCHASE, AUDIT
    reference_id = Column(Integer, nullable=True) # ID của RepairOrder nếu xuất kho cho xe
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    part = relationship("Part")
    created_by = relationship("User")

class RepairOrder(Base):
    __tablename__ = "repair_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False) # RO-2026-000001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    reception_id = Column(Integer, ForeignKey("vehicle_receptions.id"), nullable=True)
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    receptionist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    mileage_in = Column(Integer, default=0)
    mileage_out = Column(Integer, nullable=True)
    mileage_at_reception = Column(Integer, default=0)
    
    customer_complaint = Column(Text, nullable=True)
    initial_symptoms = Column(Text, nullable=True)
    technical_diagnosis = Column(Text, nullable=True)
    inspection_notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    customer_notes = Column(Text, nullable=True)
    
    status = Column(Enum(RepairOrderStatus), default=RepairOrderStatus.RECEIVED)
    
    estimated_cost = Column(Float, default=0.0)
    final_cost = Column(Float, default=0.0)
    estimated_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    
    # AI generated summary & explanations
    ai_history_summary = Column(Text, nullable=True)
    ai_service_explanation = Column(Text, nullable=True)
    ai_draft_quotation_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    vehicle = relationship("Vehicle", back_populates="repair_orders")
    technician = relationship("User", foreign_keys=[technician_id])
    receptionist = relationship("User", foreign_keys=[receptionist_id])
    customer = relationship("Customer")
    reception = relationship("VehicleReception")
    
    items = relationship("RepairOrderItem", back_populates="repair_order", cascade="all, delete-orphan")
    services = relationship("RepairOrderService", back_populates="repair_order", cascade="all, delete-orphan")
    parts = relationship("RepairOrderPart", back_populates="repair_order", cascade="all, delete-orphan")
    inspections = relationship("Inspection", back_populates="repair_order", cascade="all, delete-orphan")
    quotation = relationship("Quotation", back_populates="repair_order", uselist=False)
    invoice = relationship("Invoice", back_populates="repair_order", uselist=False)

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False)
    category = Column(Enum(InspectionCategory), default=InspectionCategory.ENGINE, nullable=False)
    item = Column(String(150), nullable=False)
    condition = Column(String(100), nullable=False)
    severity = Column(Enum(InspectionSeverity), default=InspectionSeverity.NORMAL, nullable=False)
    technician_note = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    status = Column(String(20), default="COMPLETED")
    created_at = Column(DateTime, default=datetime.utcnow)

    repair_order = relationship("RepairOrder", back_populates="inspections")

class RepairOrderService(Base):
    __tablename__ = "repair_order_services"

    id = Column(Integer, primary_key=True, index=True)
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)

    repair_order = relationship("RepairOrder", back_populates="services")
    service = relationship("Service")

class RepairOrderPart(Base):
    __tablename__ = "repair_order_parts"

    id = Column(Integer, primary_key=True, index=True)
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)

    repair_order = relationship("RepairOrder", back_populates="parts")
    part = relationship("Part")

class RepairOrderItemType(str, enum.Enum):
    SERVICE = "service"
    PART = "part"

class RepairOrderItem(Base):
    __tablename__ = "repair_order_items"

    id = Column(Integer, primary_key=True, index=True)
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False)
    item_type = Column(Enum(RepairOrderItemType), nullable=False)
    
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=True)
    
    name = Column(String(150), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)

    repair_order = relationship("RepairOrder", back_populates="items")
    service = relationship("Service")
    part = relationship("Part")

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_code = Column(String(30), unique=True, index=True, nullable=False) # QO-2026-000001
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    
    quotation_date = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True) # Ngày hết hạn
    
    subtotal = Column(Float, default=0.0) # Tiền công + linh kiện
    discount = Column(Float, default=0.0)
    vat_rate = Column(Float, default=0.10) # 10%
    vat = Column(Float, default=0.0)
    total = Column(Float, default=0.0) # subtotal - discount + vat
    
    status = Column(Enum(QuotationStatus), default=QuotationStatus.DRAFT, nullable=False)
    notes = Column(Text, nullable=True)
    
    approval_status = Column(String(20), default="PENDING")
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    customer_note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repair_order = relationship("RepairOrder", back_populates="quotation")
    customer = relationship("Customer")
    vehicle = relationship("Vehicle")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")

class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    item_type = Column(String(20), default="SERVICE") # SERVICE, PART, OTHER
    name = Column(String(150), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)

    quotation = relationship("Quotation", back_populates="items")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(30), unique=True, index=True, nullable=False) # INV-2026-000001
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    vat = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    balance_due = Column(Float, default=0.0)
    remaining_amount = Column(Float, default=0.0)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.UNPAID)
    issued_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repair_order = relationship("RepairOrder", back_populates="invoice")
    customer = relationship("Customer")
    vehicle = relationship("Vehicle")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_code = Column(String(30), unique=True, index=True, nullable=True) # PAY-2026-000001
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    amount = Column(Float, nullable=False)
    transaction_reference = Column(String(100), nullable=True)
    payment_date = Column(DateTime, default=datetime.utcnow)
    cashier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
    cashier = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False) # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, STATE_TRANSITION, PAYMENT
    resource = Column(String(50), nullable=False) # CUSTOMER, VEHICLE, REPAIR_ORDER, QUOTATION, INVOICE
    resource_id = Column(String(50), nullable=True)
    ip_address = Column(String(50), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    feature = Column(String(50), nullable=False) # history_summary, service_explainer, draft_quotation, ai_assistant
    provider = Column(String(50), default="gemini")
    model_used = Column(String(50), nullable=False)
    prompt_input = Column(Text, nullable=False)
    response_output = Column(Text, nullable=False)
    input_hash = Column(String(64), nullable=True)
    
    latency_ms = Column(Float, default=0.0)
    token_prompt_count = Column(Integer, default=0)
    token_completion_count = Column(Integer, default=0)
    token_total_count = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    status = Column(String(30), default="success") # success, failed, jailbreak_blocked
    error_message = Column(Text, nullable=True)
    
    top1_accuracy = Column(Float, default=1.0)
    parts_accuracy = Column(Float, default=1.0)
    price_variance = Column(Float, default=0.0) # Bắt buộc = 0.0%

    created_at = Column(DateTime, default=datetime.utcnow)

class CustomerRequest(Base):
    __tablename__ = "customer_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(30), unique=True, index=True, nullable=False) # REQ-YYYYMMDD-XXXX
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    license_plate = Column(String(20), index=True, nullable=False)
    vehicle_brand = Column(String(50), nullable=False)
    vehicle_model = Column(String(50), nullable=False)
    manufacture_year = Column(Integer, nullable=True)
    current_mileage = Column(Integer, default=0)
    service_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    preferred_date = Column(String(20), nullable=True)
    preferred_time = Column(String(20), nullable=True)
    note = Column(Text, nullable=True)
    
    status = Column(Enum(CustomerRequestStatus), default=CustomerRequestStatus.PENDING, nullable=False)
    admin_note = Column(Text, nullable=True)
    assigned_employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    source = Column(String(50), default="CUSTOMER_PORTAL")
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_employee = relationship("User", foreign_keys=[assigned_employee_id])
    customer = relationship("Customer")
    vehicle = relationship("Vehicle")
    appointment = relationship("Appointment")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
