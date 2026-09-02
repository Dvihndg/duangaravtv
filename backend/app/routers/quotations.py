from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Quotation, QuotationItem, QuotationStatus, User, UserRole
from backend.app.auth import get_current_user, require_roles
from backend.app.services.quotation_service import QuotationService

router = APIRouter(prefix="/quotations", tags=["Quotations"])

class QuotationItemInput(BaseModel):
    item_type: str = "SERVICE"
    name: str
    quantity: float = 1.0
    unit_price: float
    discount: float = 0.0

class CreateQuotationRequest(BaseModel):
    repair_order_id: int
    items: List[QuotationItemInput]
    discount_amount: float = 0.0
    vat_rate: float = 0.10
    valid_days: int = 15
    notes: Optional[str] = None

class ApprovalRequest(BaseModel):
    customer_note: Optional[str] = None

@router.get("")
def list_quotations(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Quotation)
    if status_filter:
        query = query.filter(Quotation.status == status_filter.lower())
    return query.order_by(Quotation.id.desc()).all()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_quotation(
    req: CreateQuotationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    items_dict = [itm.model_dump() for itm in req.items]
    qo = QuotationService.create_quotation(
        db=db,
        repair_order_id=req.repair_order_id,
        items_data=items_dict,
        discount_amount=req.discount_amount,
        vat_rate=req.vat_rate,
        valid_days=req.valid_days,
        notes=req.notes
    )
    return {
        "success": True,
        "message": "Khởi tạo báo giá dịch vụ thành công",
        "data": {
            "id": qo.id,
            "quotation_code": qo.quotation_code,
            "repair_order_id": qo.repair_order_id,
            "subtotal": qo.subtotal,
            "discount": qo.discount,
            "vat": qo.vat,
            "total": qo.total,
            "status": qo.status.value,
            "valid_until": qo.valid_until
        }
    }

@router.get("/{id}")
def get_quotation_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    qo = db.query(Quotation).filter(Quotation.id == id).first()
    if not qo:
        raise HTTPException(status_code=404, detail="Báo giá không tồn tại.")
    
    items = db.query(QuotationItem).filter(QuotationItem.quotation_id == qo.id).all()
    return {
        "id": qo.id,
        "quotation_code": qo.quotation_code,
        "repair_order_id": qo.repair_order_id,
        "customer_id": qo.customer_id,
        "vehicle_id": qo.vehicle_id,
        "subtotal": qo.subtotal,
        "discount": qo.discount,
        "vat_rate": qo.vat_rate,
        "vat": qo.vat,
        "total": qo.total,
        "status": qo.status.value,
        "valid_until": qo.valid_until,
        "items": [
            {
                "id": itm.id,
                "name": itm.name,
                "item_type": itm.item_type,
                "quantity": itm.quantity,
                "unit_price": itm.unit_price,
                "discount": itm.discount,
                "subtotal": itm.subtotal
            } for itm in items
        ]
    }

@router.post("/{id}/approve")
def approve_quotation(
    id: int,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    qo = QuotationService.approve_quotation(db, id, req.customer_note)
    return {
        "success": True,
        "message": "Báo giá đã được khách hàng phê duyệt thành công.",
        "data": {"id": qo.id, "status": qo.status.value, "approved_at": qo.approved_at}
    }

@router.post("/{id}/reject")
def reject_quotation(
    id: int,
    req: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    qo = QuotationService.reject_quotation(db, id, req.customer_note)
    return {
        "success": True,
        "message": "Đã ghi nhận khách hàng từ chối báo giá.",
        "data": {"id": qo.id, "status": qo.status.value, "rejected_at": qo.rejected_at}
    }
