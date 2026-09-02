from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import Part, InventoryTransaction, InventoryTransactionType, RepairOrder

class InventoryService:
    """
    Dịch vụ quản trị kho phụ tùng và kiểm soát xuất nhập (Inventory Service).
    Nguyên tắc vàng: Số lượng tồn kho tuyệt đối không bao giờ được phép âm (stock >= 0).
    Mọi biến động phải sinh bản ghi InventoryTransaction tương ứng trong 1 atomic transaction.
    """

    @staticmethod
    def check_stock_availability(db: Session, part_id: int, required_quantity: int) -> bool:
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part or not part.is_active:
            raise HTTPException(status_code=404, detail="Phụ tùng không tồn tại hoặc đã ngừng kinh doanh.")
        return part.stock_quantity >= required_quantity

    @staticmethod
    def export_part_for_repair_order(
        db: Session,
        part_id: int,
        quantity: int,
        repair_order_id: int,
        user_id: int = None,
        notes: str = None
    ) -> InventoryTransaction:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Số lượng xuất kho phải lớn hơn 0.")

        # Query with row-level lock where supported
        part = db.query(Part).filter(Part.id == part_id).with_for_update().first()
        if not part or not part.is_active:
            raise HTTPException(status_code=404, detail="Phụ tùng không tồn tại hoặc đã ngừng kinh doanh.")

        if part.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tồn kho không đủ để xuất. Hiện còn: {part.stock_quantity}, yêu cầu: {quantity}. Tồn kho không thể âm!"
            )

        prev_qty = part.stock_quantity
        new_qty = prev_qty - quantity
        part.stock_quantity = new_qty

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
            notes=notes or f"Xuất kho cho Phiếu sửa chữa #{repair_order_id}"
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
        user_id: int = None,
        notes: str = None
    ) -> InventoryTransaction:
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="Số lượng nhập kho phải lớn hơn 0.")

        part = db.query(Part).filter(Part.id == part_id).with_for_update().first()
        if not part:
            raise HTTPException(status_code=404, detail="Phụ tùng không tồn tại.")

        prev_qty = part.stock_quantity
        new_qty = prev_qty + quantity
        part.stock_quantity = new_qty

        tx = InventoryTransaction(
            part_id=part.id,
            transaction_type=InventoryTransactionType.IMPORT,
            quantity=quantity,
            reference_type="PURCHASE",
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            created_by_id=user_id,
            created_at=datetime.utcnow(),
            notes=notes or "Nhập kho linh kiện bổ sung"
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
        user_id: int = None,
        reason: str = None
    ) -> InventoryTransaction:
        if actual_quantity < 0:
            raise HTTPException(status_code=400, detail="Số lượng tồn kho thực tế không thể âm.")

        part = db.query(Part).filter(Part.id == part_id).with_for_update().first()
        if not part:
            raise HTTPException(status_code=404, detail="Phụ tùng không tồn tại.")

        prev_qty = part.stock_quantity
        diff = actual_quantity - prev_qty
        part.stock_quantity = actual_quantity

        tx = InventoryTransaction(
            part_id=part.id,
            transaction_type=InventoryTransactionType.ADJUSTMENT,
            quantity=abs(diff),
            reference_type="AUDIT",
            previous_quantity=prev_qty,
            new_quantity=actual_quantity,
            created_by_id=user_id,
            created_at=datetime.utcnow(),
            notes=reason or f"Kiểm kê điều chỉnh kho: {prev_qty} -> {actual_quantity}"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
