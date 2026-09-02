from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    Invoice, InvoiceStatus, Payment, PaymentMethod,
    RepairOrder, RepairOrderStatus, User, UserRole
)
from backend.app.schemas import InvoiceOut, PaymentCreate, PaymentOut
from backend.app.auth import get_current_user, require_roles
from backend.app.services.payment_service import PaymentService

router = APIRouter(tags=["Invoices & Payments"])

@router.post("/api/v1/repair-orders/{ro_id}/invoice", response_model=InvoiceOut)
@router.post("/api/v1/invoices/from-ro/{ro_id}", response_model=InvoiceOut)
def create_invoice_for_repair_order(
    ro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.CASHIER]))
):
    inv = PaymentService.create_invoice_from_repair_order(db, ro_id)
    return inv

@router.get("/api/v1/invoices", response_model=List[InvoiceOut])
def list_invoices(
    status: Optional[InvoiceStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    return query.order_by(Invoice.issued_date.desc()).all()

@router.get("/api/v1/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")
    return inv

@router.post("/api/v1/payments", response_model=PaymentOut)
def record_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.CASHIER]))
):
    payment = PaymentService.process_payment(
        db=db,
        invoice_id=payment_in.invoice_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        transaction_reference=payment_in.transaction_reference,
        cashier_id=current_user.id,
        notes=None
    )
    return payment

@router.get("/api/v1/payments", response_model=List[PaymentOut])
def list_payments(
    invoice_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.CASHIER]))
):
    query = db.query(Payment)
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    return query.order_by(Payment.payment_date.desc()).all()
