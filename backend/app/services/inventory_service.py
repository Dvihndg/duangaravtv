from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import Part, InventoryTransaction, InventoryTransactionType, RepairOrder

class InventoryService:
    """
    Dá»‹ch vá»¥ quáº£n trá»‹ kho phá»¥ tÃ¹ng vÃ  kiá»ƒm soÃ¡t xuáº¥t nháº­p (Inventory Service).
    NguyÃªn táº¯c vÃ ng: Sá»‘ lÆ°á»£ng tá»“n kho tuyá»‡t Ä‘á»‘i khÃ´ng bao giá» Ä‘Æ°á»£c phÃ©p Ã¢m (stock >= 0).
    Má»i biáº¿n Ä‘á»™ng pháº£i sinh báº£n ghi InventoryTransaction tÆ°Æ¡ng á»©ng trong 1 atomic transaction.
    """

    @staticmethod
    def check_stock_availability(db: Session, part_id: int, required_quantity: int) -> bool:
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part or not part.is_active:
            raise HTTPException(status_code=404, detail="Phá»¥ tÃ¹ng khÃ´ng tá»“n táº¡i hoáº·c Ä‘Ã£ ngá»«ng kinh doanh.")
        return part.stock_quantity >= required_quantity  # type: ignore

    @staticmethod
    def export_part_for_repair_order(
        db: Session,
        part_id: int,
        quantity: int,
        repair_order_id: int,
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> InventoryTransaction:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Sá»‘ lÆ°á»£ng xuáº¥t kho pháº£i lá»›n hÆ¡n 0.")

        # Query with row-level lock where supported
        part = db.query(Part).filter(Part.id == part_id).with_for_update().first()
        if not part or not part.is_active:
            raise HTTPException(status_code=404, detail="Phá»¥ tÃ¹ng khÃ´ng tá»“n táº¡i hoáº·c Ä‘Ã£ ngá»«ng kinh doanh.")

        if part.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tá»“n kho khÃ´ng Ä‘á»§ Ä‘á»ƒ xuáº¥t. Hiá»‡n cÃ²n: {part.stock_quantity}, yÃªu cáº§u: {quantity}. Tá»“n kho khÃ´ng thá»ƒ Ã¢m!"
            )

        prev_qty = part.stock_quantity
        new_qty = prev_qty - quantity
        part.stock_quantity = new_qty  # type: ignore

        tx = InventoryTransaction(
            part_id=part.id,
            transaction_type=InventoryTransactionType.EXPORT,
            quantity=quantity,
            reference_type="REPAIR_ORDER",
            reference_id=repair_order_id,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            created_by_id=user_id,
            created_at=datetime.utcnow(),
            notes=notes or f"Xuáº¥t kho cho Phiáº¿u sá»­a chá»¯a #{repair_order_id}"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def import_stock(
        db: Session,
        part_id: int,
        quantity: int,
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> InventoryTransaction:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Sá»‘ lÆ°á»£ng nháº­p kho pháº£i lá»›n hÆ¡n 0.")

        part = db.query(Part).filter(Part.id == part_id).with_for_update().first()
        if not part:
            raise HTTPException(status_code=404, detail="Phá»¥ tÃ¹ng khÃ´ng tá»“n táº¡i.")

        prev_qty = part.stock_quantity
        new_qty = prev_qty + quantity
        part.stock_quantity = new_qty  # type: ignore

        tx = InventoryTransaction(
            part_id=part.id,
            transaction_type=InventoryTransactionType.IMPORT,
            quantity=quantity,
            reference_type="PURCHASE",
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            created_by_id=user_id,
            created_at=datetime.utcnow(),
            notes=notes or "Nháº­p kho linh kiá»‡n bá»• sung"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def adjust_stock(
        db: Session,
        part_id: int,
        actual_quantity: int,
        user_id: Optional[int] = None,
        reason: Optional[str] = None
    ) -> InventoryTransaction:
        if actual_quantity < 0:
            raise HTTPException(status_code=400, detail="Sá»‘ lÆ°á»£ng tá»“n kho thá»±c táº¿ khÃ´ng thá»ƒ Ã¢m.")

        part = db.query(Part).filter(Part.id == part_id).with_for_update().first()
        if not part:
            raise HTTPException(status_code=404, detail="Phá»¥ tÃ¹ng khÃ´ng tá»“n táº¡i.")

        prev_qty = part.stock_quantity
        diff = actual_quantity - prev_qty
        part.stock_quantity = actual_quantity  # type: ignore

        tx = InventoryTransaction(
            part_id=part.id,
            transaction_type=InventoryTransactionType.ADJUSTMENT,
            quantity=abs(diff),
            reference_type="AUDIT",
            previous_quantity=prev_qty,
            new_quantity=actual_quantity,
            created_by_id=user_id,
            created_at=datetime.utcnow(),
            notes=reason or f"Kiá»ƒm kÃª Ä‘iá»u chá»‰nh kho: {prev_qty} -> {actual_quantity}"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
