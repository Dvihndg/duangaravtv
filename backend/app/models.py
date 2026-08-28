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
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class RepairOrderStatus(str, enum.Enum):
    RECEIVED = "received"        # Tiếp nhận
    DIAGNOSING = "diagnosing"    # Chẩn đoán Lỗi
    QUOTED = "quoted"            # Đã Báo giá
    APPROVED = "approved"        # Khách duyệt Báo giá
    IN_PROGRESS = "in_progress"  # Đang sửa chữa
    FINISHED = "finished"        # Hoàn thành sửa chữa
    INVOICED = "invoiced"        # Đã lập hóa đơn

class InvoiceStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"

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
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, index=True, nullable=False) # Biển số xe
    brand = Column(String(50), nullable=False) # Hãng xe (Toyota, Honda, BMW...)
    model = Column(String(50), nullable=False) # Dòng xe (Camry, Civic, X5...)
    year = Column(Integer, nullable=True) # Năm sản xuất
    color = Column(String(30), nullable=True)
    vin_number = Column(String(50), nullable=True) # Số khung
    current_mileage = Column(Integer, default=0) # Số km hiện tại
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    owner = relationship("Customer", back_populates="vehicles")
    appointments = relationship("Appointment", back_populates="vehicle")
    repair_orders = relationship("RepairOrder", back_populates="vehicle")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True) # Yêu cầu của khách
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    assigned_technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="appointments")
    technician = relationship("User", foreign_keys=[assigned_technician_id])

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False) # VD: SER-001
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="Bảo dưỡng")
    description = Column(Text, nullable=True)
    labor_cost = Column(Float, default=0.0) # Chi phí công sửa chữa
    estimated_hours = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)

class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False) # VD: PAR-001
    name = Column(String(150), nullable=False)
    brand = Column(String(50), nullable=True)
    unit_price = Column(Float, default=0.0) # Đơn giá bán
    cost_price = Column(Float, default=0.0) # Giá nhập
    stock_quantity = Column(Integer, default=0)
    min_stock_alert = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)

class RepairOrder(Base):
    __tablename__ = "repair_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False) # VD: RO-2026-001
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    receptionist_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    mileage_at_reception = Column(Integer, default=0)
    initial_symptoms = Column(Text, nullable=True) # Tình trạng ban đầu khi nhận xe
    technical_diagnosis = Column(Text, nullable=True) # Ghi chú chẩn đoán của KTV
    
    status = Column(Enum(RepairOrderStatus), default=RepairOrderStatus.RECEIVED)
    
    estimated_cost = Column(Float, default=0.0)
    final_cost = Column(Float, default=0.0)
    
    # AI generated summary & explanations
    ai_history_summary = Column(Text, nullable=True)
    ai_service_explanation = Column(Text, nullable=True)
    ai_draft_quotation_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    vehicle = relationship("Vehicle", back_populates="repair_orders")
    technician = relationship("User", foreign_keys=[technician_id])
    receptionist = relationship("User", foreign_keys=[receptionist_id])
    items = relationship("RepairOrderItem", back_populates="repair_order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="repair_order", uselist=False)

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

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(30), unique=True, index=True, nullable=False) # VD: INV-2026-001
    repair_order_id = Column(Integer, ForeignKey("repair_orders.id"), nullable=False, unique=True)
    
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    balance_due = Column(Float, default=0.0)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.UNPAID)
    issued_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)

    repair_order = relationship("RepairOrder", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    amount = Column(Float, nullable=False)
    transaction_reference = Column(String(100), nullable=True)
    payment_date = Column(DateTime, default=datetime.utcnow)
    cashier_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
    cashier = relationship("User")

class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    feature = Column(String(50), nullable=False) # history_summary, service_explainer, draft_quotation
    prompt_input = Column(Text, nullable=False)
    response_output = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
