from datetime import datetime, timezone
from typing import Set, Dict, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import RepairOrder, RepairOrderStatus

class RepairOrderService:
    """
    DÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¹ch vÃƒÂ¡Ã‚Â»Ã‚Â¥ quÃƒÂ¡Ã‚ÂºÃ‚Â£n trÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¹ VÃƒÆ’Ã‚Â²ng Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã‚Âi PhiÃƒÂ¡Ã‚ÂºÃ‚Â¿u SÃƒÂ¡Ã‚Â»Ã‚Â­a ChÃƒÂ¡Ã‚Â»Ã‚Â¯a (State Machine Service).
    NgÃƒâ€žÃ†â€™n chÃƒÂ¡Ã‚ÂºÃ‚Â·n tuyÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡t Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã¢â‚¬Ëœi viÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡c chuyÃƒÂ¡Ã‚Â»Ã†â€™n Ãƒâ€žÃ¢â‚¬ËœÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¢i trÃƒÂ¡Ã‚ÂºÃ‚Â¡ng thÃƒÆ’Ã‚Â¡i phi quy tÃƒÂ¡Ã‚ÂºÃ‚Â¯c.
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
        RepairOrderStatus.COMPLETED: set(), # TrÃƒÂ¡Ã‚ÂºÃ‚Â¡ng thÃƒÆ’Ã‚Â¡i kÃƒÂ¡Ã‚ÂºÃ‚Â¿t thÃƒÆ’Ã‚Âºc
        RepairOrderStatus.CANCELLED: set()  # TrÃƒÂ¡Ã‚ÂºÃ‚Â¡ng thÃƒÆ’Ã‚Â¡i kÃƒÂ¡Ã‚ÂºÃ‚Â¿t thÃƒÆ’Ã‚Âºc
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
        user_id: Optional[int] = None
    ) -> RepairOrder:
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            raise HTTPException(status_code=404, detail="PhiÃƒÂ¡Ã‚ÂºÃ‚Â¿u sÃƒÂ¡Ã‚Â»Ã‚Â­a chÃƒÂ¡Ã‚Â»Ã‚Â¯a khÃƒÆ’Ã‚Â´ng tÃƒÂ¡Ã‚Â»Ã¢â‚¬Å“n tÃƒÂ¡Ã‚ÂºÃ‚Â¡i.")

        if not cls.can_transition(ro.status, new_status):  # type: ignore
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ChuyÃƒÂ¡Ã‚Â»Ã†â€™n trÃƒÂ¡Ã‚ÂºÃ‚Â¡ng thÃƒÆ’Ã‚Â¡i khÃƒÆ’Ã‚Â´ng hÃƒÂ¡Ã‚Â»Ã‚Â£p lÃƒÂ¡Ã‚Â»Ã¢â‚¬Â¡: KhÃƒÆ’Ã‚Â´ng thÃƒÂ¡Ã‚Â»Ã†â€™ chuyÃƒÂ¡Ã‚Â»Ã†â€™n tÃƒÂ¡Ã‚Â»Ã‚Â« '{ro.status.value}' sang '{new_status.value}'. Vui lÃƒÆ’Ã‚Â²ng tuÃƒÆ’Ã‚Â¢n thÃƒÂ¡Ã‚Â»Ã‚Â§ quy trÃƒÆ’Ã‚Â¬nh tuÃƒÂ¡Ã‚ÂºÃ‚Â§n tÃƒÂ¡Ã‚Â»Ã‚Â±."
            )

        ro.status = new_status  # type: ignore
        if new_status == RepairOrderStatus.COMPLETED:
            ro.completed_at = datetime.now(timezone.utc)  # type: ignore

        db.commit()
        db.refresh(ro)
        return ro
