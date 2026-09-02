from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import (
    Quotation, QuotationItem, QuotationStatus, RepairOrder, 
    RepairOrderStatus, Customer, Vehicle
)

DEFAULT_VAT_RATE = 0.10

class QuotationService:
    """
    Dịch vụ tính toán và quản lý báo giá dịch vụ (Quotation Service).
    Nguyên tắc bất biến: Toàn bộ số tiền (subtotal, discount, VAT, total) 
    phải được tính toán tại Server-side, tuyệt đối không tin tưởng dữ liệu tiền từ Client.
    """

    @staticmethod
    def calculate_totals(
        items: List[Dict[str, Any]], 
        discount_amount: float = 0.0, 
        vat_rate: float = DEFAULT_VAT_RATE
    ) -> Dict[str, float]:
        """
        Tính toán tài chính chuẩn xác:
        Labor + Parts = Subtotal
        Taxable = Subtotal - Discount
        VAT = Taxable * vat_rate
        Total = Taxable + VAT
        """
        subtotal = sum(float(item.get("unit_price", 0.0)) * float(item.get("quantity", 1.0)) for item in items)
        discount = max(0.0, float(discount_amount))
        taxable_amount = max(0.0, subtotal - discount)
        vat = round(taxable_amount * float(vat_rate), 2)
        total = round(taxable_amount + vat, 2)

        return {
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "taxable_amount": round(taxable_amount, 2),
            "vat_rate": float(vat_rate),
            "vat": vat,
            "total": total
        }

    @staticmethod
    def create_quotation(
        db: Session,
        repair_order_id: int,
        items_data: List[Dict[str, Any]],
        discount_amount: float = 0.0,
        vat_rate: float = DEFAULT_VAT_RATE,
        valid_days: int = 15,
        notes: str = None
    ) -> Quotation:
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại.")

        # Check existing quotation
        existing_qo = db.query(Quotation).filter(Quotation.repair_order_id == repair_order_id).first()
        if existing_qo and existing_qo.status in [QuotationStatus.APPROVED]:
            raise HTTPException(status_code=400, detail="Phiếu sửa chữa đã có báo giá được phê duyệt.")

        calc = QuotationService.calculate_totals(items_data, discount_amount, vat_rate)
        
        now = datetime.utcnow()
        valid_until = now + timedelta(days=valid_days)
        
        # Sinh mã QO-YYYY-XXXXXX
        today_str = now.strftime("%Y%m%d")
        qo_code = f"QO-{today_str}-{ro.id:04d}"

        if existing_qo:
            # Update existing draft
            existing_qo.subtotal = calc["subtotal"]
            existing_qo.discount = calc["discount"]
            existing_qo.vat_rate = calc["vat_rate"]
            existing_qo.vat = calc["vat"]
            existing_qo.total = calc["total"]
            existing_qo.valid_until = valid_until
            existing_qo.notes = notes
            existing_qo.status = QuotationStatus.PENDING_APPROVAL
            
            # Recreate items
            db.query(QuotationItem).filter(QuotationItem.quotation_id == existing_qo.id).delete()
            for itm in items_data:
                item_sub = float(itm.get("unit_price", 0.0)) * float(itm.get("quantity", 1.0))
                qo_item = QuotationItem(
                    quotation_id=existing_qo.id,
                    item_type=itm.get("item_type", "SERVICE"),
                    name=itm.get("name", "Dịch vụ"),
                    quantity=float(itm.get("quantity", 1.0)),
                    unit_price=float(itm.get("unit_price", 0.0)),
                    discount=float(itm.get("discount", 0.0)),
                    subtotal=round(item_sub, 2)
                )
                db.add(qo_item)
            
            db.commit()
            db.refresh(existing_qo)
            return existing_qo

        new_qo = Quotation(
            quotation_code=qo_code,
            repair_order_id=ro.id,
            customer_id=ro.customer_id or ro.vehicle.customer_id,
            vehicle_id=ro.vehicle_id,
            quotation_date=now,
            valid_until=valid_until,
            subtotal=calc["subtotal"],
            discount=calc["discount"],
            vat_rate=calc["vat_rate"],
            vat=calc["vat"],
            total=calc["total"],
            status=QuotationStatus.PENDING_APPROVAL,
            notes=notes
        )
        db.add(new_qo)
        db.flush()

        for itm in items_data:
            item_sub = float(itm.get("unit_price", 0.0)) * float(itm.get("quantity", 1.0))
            qo_item = QuotationItem(
                quotation_id=new_qo.id,
                item_type=itm.get("item_type", "SERVICE"),
                name=itm.get("name", "Dịch vụ"),
                quantity=float(itm.get("quantity", 1.0)),
                unit_price=float(itm.get("unit_price", 0.0)),
                discount=float(itm.get("discount", 0.0)),
                subtotal=round(item_sub, 2)
            )
            db.add(qo_item)

        ro.estimated_cost = calc["total"]
        ro.status = RepairOrderStatus.WAITING_CUSTOMER_APPROVAL
        db.commit()
        db.refresh(new_qo)
        return new_qo

    @staticmethod
    def approve_quotation(db: Session, quotation_id: int, customer_note: str = None) -> Quotation:
        qo = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not qo:
            raise HTTPException(status_code=404, detail="Báo giá không tồn tại.")

        if qo.status == QuotationStatus.APPROVED:
            return qo

        if qo.valid_until and qo.valid_until < datetime.utcnow():
            qo.status = QuotationStatus.EXPIRED
            db.commit()
            raise HTTPException(status_code=400, detail="Báo giá đã hết hạn, không thể phê duyệt.")

        qo.status = QuotationStatus.APPROVED
        qo.approval_status = "APPROVED"
        qo.approved_at = datetime.utcnow()
        qo.customer_note = customer_note

        # Automatically advance RO to APPROVED
        if qo.repair_order:
            qo.repair_order.status = RepairOrderStatus.APPROVED
            qo.repair_order.final_cost = qo.total

        db.commit()
        db.refresh(qo)
        return qo

    @staticmethod
    def reject_quotation(db: Session, quotation_id: int, customer_note: str = None) -> Quotation:
        qo = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not qo:
            raise HTTPException(status_code=404, detail="Báo giá không tồn tại.")

        qo.status = QuotationStatus.REJECTED
        qo.approval_status = "REJECTED"
        qo.rejected_at = datetime.utcnow()
        qo.customer_note = customer_note

        if qo.repair_order:
            qo.repair_order.status = RepairOrderStatus.CANCELLED

        db.commit()
        db.refresh(qo)
        return qo
