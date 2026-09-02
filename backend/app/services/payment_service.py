from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import Invoice, InvoiceStatus, Payment, PaymentMethod, RepairOrder, RepairOrderStatus

class PaymentService:
    """
    Dịch vụ quản trị Hóa đơn và Thanh toán (Payment & Invoice Service).
    Nguyên tắc vàng:
    1. Số tiền thanh toán phải > 0 và <= số tiền còn lại của hóa đơn (balance_due).
    2. Hóa đơn đã HỦY (CANCELLED) tuyệt đối không được ghi nhận thanh toán.
    3. Việc tạo Payment và cập nhật số dư Hóa đơn phải nằm trong 1 Atomic Transaction.
    """

    @staticmethod
    def create_invoice_from_repair_order(db: Session, repair_order_id: int) -> Invoice:
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại.")

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

        now = datetime.utcnow()
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
        transaction_reference: str = None,
        cashier_id: int = None,
        notes: str = None
    ) -> Payment:
        # Atomic lock on invoice
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).with_for_update().first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Hóa đơn không tồn tại.")

        if invoice.status == InvoiceStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hóa đơn đã bị HỦY (CANCELLED), không thể ghi nhận thanh toán!"
            )

        if invoice.status == InvoiceStatus.PAID or invoice.balance_due <= 0.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hóa đơn này đã được thanh toán đầy đủ!"
            )

        pay_amount = round(float(amount), 2)
        if pay_amount <= 0.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số tiền thanh toán phải lớn hơn 0 VNĐ."
            )

        remaining_balance = round(invoice.balance_due, 2)
        if pay_amount > remaining_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số tiền thanh toán ({pay_amount:,.0f} VNĐ) không được vượt quá số dư còn lại ({remaining_balance:,.0f} VNĐ)!"
            )

        now = datetime.utcnow()
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
        new_paid = round(invoice.paid_amount + pay_amount, 2)
        new_balance = round(invoice.total_amount - new_paid, 2)

        invoice.paid_amount = new_paid
        invoice.balance_due = max(0.0, new_balance)
        invoice.remaining_amount = max(0.0, new_balance)

        if new_balance <= 0.0:
            invoice.status = InvoiceStatus.PAID
            # Advance RO to COMPLETED if not already
            if invoice.repair_order and invoice.repair_order.status != RepairOrderStatus.CANCELLED:
                invoice.repair_order.status = RepairOrderStatus.COMPLETED
                invoice.repair_order.completed_at = now
        else:
            invoice.status = InvoiceStatus.PARTIAL

        db.commit()
        db.refresh(payment)
        db.refresh(invoice)
        return payment
