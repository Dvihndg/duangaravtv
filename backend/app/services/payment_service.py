from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import Invoice, InvoiceStatus, Payment, PaymentMethod, RepairOrder, RepairOrderStatus

class PaymentService:
    """
    DÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¹ch vÃƒÂ¡Ã‚Â»Ã‚Â¥ quÃƒÂ¡Ã‚ÂºÃ‚Â£n trÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¹ HÃƒÆ’Ã‚Â³a Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â¡n vÃƒÆ’Ã‚Â  Thanh toÃƒÆ’Ã‚Â¡n (Payment & Invoice Service).
    NguyÃƒÆ’Ã‚Âªn tÃƒÂ¡Ã‚ÂºÃ‚Â¯c vÃƒÆ’Ã‚Â ng:
    1. SÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœ tiÃƒÂ¡Ã‚Â»Ã‚Ân thanh toÃƒÆ’Ã‚Â¡n phÃƒÂ¡Ã‚ÂºÃ‚Â£i > 0 vÃƒÆ’Ã‚Â  <= sÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœ tiÃƒÂ¡Ã‚Â»Ã‚Ân cÃƒÆ’Ã‚Â²n lÃƒÂ¡Ã‚ÂºÃ‚Â¡i cÃƒÂ¡Ã‚Â»Ã‚Â§a hÃƒÆ’Ã‚Â³a Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â¡n (balance_due).
    2. HÃƒÆ’Ã‚Â³a Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â¡n Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Â£ HÃƒÂ¡Ã‚Â»Ã‚Â¦Y (CANCELLED) tuyÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœi khÃƒÆ’Ã‚Â´ng Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c ghi nhÃƒÂ¡Ã‚ÂºÃ‚Â­n thanh toÃƒÆ’Ã‚Â¡n.
    3. ViÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡c tÃƒÂ¡Ã‚ÂºÃ‚Â¡o Payment vÃƒÆ’Ã‚Â  cÃƒÂ¡Ã‚ÂºÃ‚Â­p nhÃƒÂ¡Ã‚ÂºÃ‚Â­t sÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœ dÃƒâ€ Ã‚Â° HÃƒÆ’Ã‚Â³a Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â¡n phÃƒÂ¡Ã‚ÂºÃ‚Â£i nÃƒÂ¡Ã‚ÂºÃ‚Â±m trong 1 Atomic Transaction.
    """

    @staticmethod
    def create_invoice_from_repair_order(db: Session, repair_order_id: int) -> Invoice:
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            raise HTTPException(status_code=404, detail="PhiÃƒÂ¡Ã‚ÂºÃ‚Â¿u sÃƒÂ¡Ã‚Â»Ã‚Â­a chÃƒÂ¡Ã‚Â»Ã‚Â¯a khÃƒÆ’Ã‚Â´ng tÃƒÂ¡Ã‚Â»Ã¢â‚¬Å“n tÃƒÂ¡Ã‚ÂºÃ‚Â¡i.")

        existing_inv = db.query(Invoice).filter(Invoice.repair_order_id == repair_order_id).first()
        if existing_inv:
            return existing_inv

        # Retrieve total from Quotation or items
        total_amount = ro.final_cost or ro.estimated_cost or 0.0
        if total_amount <= 0.0:
            # Calculate from items
            services_sum = sum(s.subtotal for s in ro.services) if ro.services else 0.0
            parts_sum = sum(p.subtotal for p in ro.parts) if ro.parts else 0.0
            sub = services_sum + parts_sum
            vat = round(sub * 0.10, 2)
            total_amount = sub + vat

        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y%m%d")
        inv_code = f"INV-{today_str}-{ro.id:04d}"

        new_inv = Invoice(
            invoice_number=inv_code,
            repair_order_id=ro.id,
            customer_id=ro.customer_id or (ro.vehicle.customer_id if ro.vehicle else None),
            vehicle_id=ro.vehicle_id,
            invoice_date=now,
            subtotal=round(total_amount / 1.10, 2),
            tax_amount=round(total_amount - (total_amount / 1.10), 2),
            vat=round(total_amount - (total_amount / 1.10), 2),
            total_amount=round(total_amount, 2),
            total=round(total_amount, 2),
            paid_amount=0.0,
            balance_due=round(total_amount, 2),
            remaining_amount=round(total_amount, 2),
            status=InvoiceStatus.UNPAID
        )
        db.add(new_inv)
        db.commit()
        db.refresh(new_inv)
        return new_inv

    @staticmethod
    def process_payment(
        db: Session,
        invoice_id: int,
        amount: float,
        payment_method: PaymentMethod = PaymentMethod.CASH,
        transaction_reference: Optional[str] = None,
        cashier_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Payment:
        # Atomic lock on invoice
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).with_for_update().first()
        if not invoice:
            raise HTTPException(status_code=404, detail="HÃƒÆ’Ã‚Â³a Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â¡n khÃƒÆ’Ã‚Â´ng tÃƒÂ¡Ã‚Â»Ã¢â‚¬Å“n tÃƒÂ¡Ã‚ÂºÃ‚Â¡i.")

        if invoice.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hóa đơn đã bị HỦY (CANCELLED), không thể ghi nhận thanh toán!"
            )

        if invoice.status == InvoiceStatus.PAID or invoice.balance_due <= 0.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HÃƒÆ’Ã‚Â³a Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â¡n nÃƒÆ’Ã‚Â y Ãƒâ€žÃ¢â‚¬ËœÃƒÆ’Ã‚Â£ Ãƒâ€žÃ¢â‚¬ËœÃƒâ€ Ã‚Â°ÃƒÂ¡Ã‚Â»Ã‚Â£c thanh toÃƒÆ’Ã‚Â¡n Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚ÂºÃ‚Â§y Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã‚Â§!"
            )

        pay_amount = round(float(amount), 2)
        if pay_amount <= 0.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœ tiÃƒÂ¡Ã‚Â»Ã‚Ân thanh toÃƒÆ’Ã‚Â¡n phÃƒÂ¡Ã‚ÂºÃ‚Â£i lÃƒÂ¡Ã‚Â»Ã¢â‚¬Âºn hÃƒâ€ Ã‚Â¡n 0 VNÃƒâ€žÃ‚Â."
            )

        remaining_balance = round(invoice.balance_due, 2)  # type: ignore
        if pay_amount > remaining_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số tiền thanh toán ({pay_amount:,.0f} VNĐ) không được vượt quá số dư còn lại ({remaining_balance:,.0f} VNĐ)!"
            )

        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y%m%d")
        pay_code = f"PAY-{today_str}-{invoice.id:04d}-{int(now.timestamp()) % 10000:04d}"

        # Create payment record
        payment = Payment(
            payment_code=pay_code,
            invoice_id=invoice.id,
            payment_method=payment_method,
            amount=pay_amount,
            transaction_reference=transaction_reference,
            payment_date=now,
            cashier_id=cashier_id,
            notes=notes
        )
        db.add(payment)

        # Update invoice balance
        new_paid = round(invoice.paid_amount + pay_amount, 2)  # type: ignore
        new_balance = round(invoice.total_amount - new_paid, 2)

        invoice.paid_amount = new_paid
        invoice.balance_due = max(0.0, new_balance)  # type: ignore
        invoice.remaining_amount = max(0.0, new_balance)  # type: ignore

        if new_balance <= 0.0:
            invoice.status = InvoiceStatus.PAID  # type: ignore
            # Advance RO to COMPLETED if not already
            if invoice.repair_order and invoice.repair_order.status != RepairOrderStatus.CANCELLED:
                invoice.repair_order.status = RepairOrderStatus.COMPLETED  # type: ignore
                invoice.repair_order.completed_at = now  # type: ignore
        else:
            invoice.status = InvoiceStatus.PARTIAL  # type: ignore

        db.commit()
        db.refresh(payment)
        db.refresh(invoice)
        return payment
