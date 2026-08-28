from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    Invoice, InvoiceStatus, Payment, PaymentMethod,
    RepairOrder, RepairOrderStatus, User, UserRole
)
from backend.app.schemas import InvoiceOut, PaymentCreate, PaymentOut
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/v1", tags=["Invoices & Payments"])

def generate_invoice_number(db: Session) -> str:
    today_str = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(Invoice).filter(Invoice.invoice_number.like(f"INV-{today_str}-%")).count()
    return f"INV-{today_str}-{(count + 1):03d}"

@router.post("/repair-orders/{ro_id}/invoice", response_model=InvoiceOut)
def create_invoice_for_repair_order(
    ro_id: int,
    discount_amount: float = 0.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.CASHIER, UserRole.RECEPTIONIST]))
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa")

    if ro.invoice:
        return ro.invoice

    subtotal = sum([item.total_price for item in ro.items])
    if subtotal == 0 and ro.final_cost > 0:
        subtotal = ro.final_cost

    tax_amount = (subtotal - discount_amount) * 0.08 # 8% VAT
    total_amount = (subtotal - discount_amount) + tax_amount

    inv_num = generate_invoice_number(db)
    invoice = Invoice(
        invoice_number=inv_num,
        repair_order_id=ro_id,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        paid_amount=0.0,
        balance_due=total_amount,
        status=InvoiceStatus.UNPAID
    )

    ro.status = RepairOrderStatus.INVOICED
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("/invoices", response_model=List[InvoiceOut])
def list_invoices(
    status: Optional[InvoiceStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    return query.order_by(Invoice.issued_date.desc()).all()

@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")
    return inv

@router.post("/payments", response_model=PaymentOut)
def record_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.CASHIER]))
):
    invoice = db.query(Invoice).filter(Invoice.id == payment_in.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn thanh toán")

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Hóa đơn này đã được thanh toán hoàn tất")

    payment = Payment(
        invoice_id=payment_in.invoice_id,
        payment_method=payment_in.payment_method,
        amount=payment_in.amount,
        transaction_reference=payment_in.transaction_reference,
        cashier_id=current_user.id
    )
    db.add(payment)

    # Update invoice balances
    invoice.paid_amount += payment_in.amount
    invoice.balance_due = max(0.0, invoice.total_amount - invoice.paid_amount)

    if invoice.balance_due <= 0:
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIAL

    db.commit()
    db.refresh(payment)
    return payment
