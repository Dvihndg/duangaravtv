from datetime import datetime
from typing import Set, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import RepairOrder, RepairOrderStatus

class RepairOrderService:
    """
    Dịch vụ quản trị Vòng đời Phiếu Sửa Chữa (State Machine Service).
    Ngăn chặn tuyệt đối việc chuyển đổi trạng thái phi quy tắc.
    """

    ALLOWED_TRANSITIONS: Dict[RepairOrderStatus, Set[RepairOrderStatus]] = {
        RepairOrderStatus.DRAFT: {RepairOrderStatus.RECEIVED, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.RECEIVED: {RepairOrderStatus.INSPECTING, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.INSPECTING: {RepairOrderStatus.QUOTATION_PENDING, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.QUOTATION_PENDING: {RepairOrderStatus.WAITING_CUSTOMER_APPROVAL, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.WAITING_CUSTOMER_APPROVAL: {RepairOrderStatus.APPROVED, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.APPROVED: {RepairOrderStatus.IN_REPAIR, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.IN_REPAIR: {RepairOrderStatus.WAITING_PARTS, RepairOrderStatus.QUALITY_CHECK, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.WAITING_PARTS: {RepairOrderStatus.IN_REPAIR, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.QUALITY_CHECK: {RepairOrderStatus.COMPLETED, RepairOrderStatus.IN_REPAIR, RepairOrderStatus.CANCELLED},
        RepairOrderStatus.COMPLETED: set(), # Trạng thái kết thúc
        RepairOrderStatus.CANCELLED: set()  # Trạng thái kết thúc
    }

    @classmethod
    def can_transition(cls, current: RepairOrderStatus, target: RepairOrderStatus) -> bool:
        if current == target:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(current, set())
        return target in allowed

    @classmethod
    def transition_status(
        cls, 
        db: Session, 
        repair_order_id: int, 
        new_status: RepairOrderStatus,
        user_id: int = None
    ) -> RepairOrder:
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại.")

        if not cls.can_transition(ro.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chuyển trạng thái không hợp lệ: Không thể chuyển từ '{ro.status.value}' sang '{new_status.value}'. Vui lòng tuân thủ quy trình tuần tự."
            )

        ro.status = new_status
        if new_status == RepairOrderStatus.COMPLETED:
            ro.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(ro)
        return ro
