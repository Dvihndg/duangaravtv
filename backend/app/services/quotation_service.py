from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import (
    Quotation, QuotationItem, QuotationStatus, RepairOrder, 
    RepairOrderStatus, Customer, Vehicle
)

DEFAULT_VAT_RATE = 0.10


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalize SQLite naive and PostgreSQL aware datetimes to UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

class QuotationService:
    """
    DÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¹ch vÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â¥ tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­nh toÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡n vÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  quÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â£n lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â½ bÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡o giÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ dÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¹ch vÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â¥ (Quotation Service).
    NguyÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªn tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¯c bÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¥t biÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¿n: ToÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â n bÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ sÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“ tiÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Ân (subtotal, discount, VAT, total) 
    phÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â£i ÃƒÆ’Ã¢â‚¬Å¾ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“ÃƒÆ’Ã¢â‚¬Â Ãƒâ€šÃ‚Â°ÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â£c tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­nh toÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡n tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¡i Server-side, tuyÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¡t ÃƒÆ’Ã¢â‚¬Å¾ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“ÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“i khÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´ng tin tÃƒÆ’Ã¢â‚¬Â Ãƒâ€šÃ‚Â°ÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€¦Ã‚Â¸ng dÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â¯ liÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¡u tiÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Ân tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â« Client.
    """

    @staticmethod
    def calculate_totals(
        items: List[Dict[str, Any]], 
        discount_amount: float = 0.0, 
        vat_rate: float = DEFAULT_VAT_RATE
    ) -> Dict[str, float]:
        """
        TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­nh toÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡n tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â i chÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­nh chuÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â©n xÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡c:
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
        notes: Optional[str] = None
    ) -> Quotation:
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            raise HTTPException(status_code=404, detail="PhiÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¿u sÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â­a chÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â¯a khÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´ng tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œn tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¡i.")

        # Check existing quotation
        existing_qo = db.query(Quotation).filter(Quotation.repair_order_id == repair_order_id).first()
        if existing_qo and existing_qo.status in [QuotationStatus.APPROVED]:
            raise HTTPException(status_code=400, detail="Báo giá đã hết hạn, không thể phê duyệt.")

        calc = QuotationService.calculate_totals(items_data, discount_amount, vat_rate)
        
        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(days=valid_days)
        
        # Sinh mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£ QO-YYYY-XXXXXX
        today_str = now.strftime("%Y%m%d")
        qo_code = f"QO-{today_str}-{ro.id:04d}"

        if existing_qo:
            # Update existing draft
            existing_qo.subtotal = calc["subtotal"]  # type: ignore
            existing_qo.discount = calc["discount"]  # type: ignore
            existing_qo.vat_rate = calc["vat_rate"]  # type: ignore
            existing_qo.vat = calc["vat"]  # type: ignore
            existing_qo.total = calc["total"]  # type: ignore
            existing_qo.valid_until = valid_until  # type: ignore
            existing_qo.notes = notes  # type: ignore
            existing_qo.status = QuotationStatus.PENDING_APPROVAL  # type: ignore
            
            # Recreate items
            db.query(QuotationItem).filter(QuotationItem.quotation_id == existing_qo.id).delete()
            for itm in items_data:
                item_sub = float(itm.get("unit_price", 0.0)) * float(itm.get("quantity", 1.0))
                qo_item = QuotationItem(
                    quotation_id=existing_qo.id,
                    item_type=itm.get("item_type", "SERVICE"),
                    name=itm.get("name", "DÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¹ch vÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â¥"),
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
                name=itm.get("name", "DÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¹ch vÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»Ãƒâ€šÃ‚Â¥"),
                quantity=float(itm.get("quantity", 1.0)),
                unit_price=float(itm.get("unit_price", 0.0)),
                discount=float(itm.get("discount", 0.0)),
                subtotal=round(item_sub, 2)
            )
            db.add(qo_item)

        ro.estimated_cost = calc["total"]  # type: ignore
        ro.status = RepairOrderStatus.WAITING_CUSTOMER_APPROVAL  # type: ignore
        db.commit()
        db.refresh(new_qo)
        return new_qo

    @staticmethod
    def approve_quotation(db: Session, quotation_id: int, customer_note: Optional[str] = None) -> Quotation:
        qo = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not qo:
            raise HTTPException(status_code=404, detail="BÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡o giÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ khÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´ng tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œn tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¡i.")

        if qo.status == QuotationStatus.APPROVED:
            return qo

        valid_until = as_utc(qo.valid_until)
        if valid_until and valid_until < datetime.now(timezone.utc):
            qo.status = QuotationStatus.EXPIRED  # type: ignore
            db.commit()
            raise HTTPException(status_code=400, detail="Báo giá đã hết hạn, không thể phê duyệt.")

        qo.status = QuotationStatus.APPROVED  # type: ignore
        qo.approval_status = "APPROVED"  # type: ignore
        qo.approved_at = datetime.now(timezone.utc)  # type: ignore
        qo.customer_note = customer_note  # type: ignore

        # Automatically advance RO to APPROVED
        if qo.repair_order:
            qo.repair_order.status = RepairOrderStatus.APPROVED  # type: ignore
            qo.repair_order.final_cost = qo.total  # type: ignore

        db.commit()
        db.refresh(qo)
        return qo

    @staticmethod
    def reject_quotation(db: Session, quotation_id: int, customer_note: Optional[str] = None) -> Quotation:
        qo = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not qo:
            raise HTTPException(status_code=404, detail="BÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡o giÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ khÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´ng tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚Â»ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œn tÃƒÆ’Ã‚Â¡Ãƒâ€šÃ‚ÂºÃƒâ€šÃ‚Â¡i.")

        qo.status = QuotationStatus.REJECTED  # type: ignore
        qo.approval_status = "REJECTED"  # type: ignore
        qo.rejected_at = datetime.now(timezone.utc)  # type: ignore
        qo.customer_note = customer_note  # type: ignore

        if qo.repair_order:
            qo.repair_order.status = RepairOrderStatus.CANCELLED  # type: ignore

        db.commit()
        db.refresh(qo)
        return qo
