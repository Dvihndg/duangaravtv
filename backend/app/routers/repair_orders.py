from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    RepairOrder, RepairOrderStatus, RepairOrderItem, RepairOrderItemType,
    Vehicle, Service, Part, User, UserRole, Invoice, InvoiceStatus,
    Inspection, InspectionCategory, InspectionSeverity, RepairOrderService, RepairOrderPart
)
from backend.app.schemas import (
    RepairOrderCreate, RepairOrderUpdate, RepairOrderOut,
    RepairOrderItemCreate, RepairOrderItemOut
)
from backend.app.auth import get_current_user, require_roles
from backend.app.services.repair_order_service import RepairOrderService as ROService
from backend.app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/v1/repair-orders", tags=["Repair Orders"])

class StatusUpdateRequest(BaseModel):
    status: RepairOrderStatus

class AssignTechnicianRequest(BaseModel):
    technician_id: int

class InspectionItemRequest(BaseModel):
    category: InspectionCategory = InspectionCategory.ENGINE
    item: str
    condition: str
    severity: InspectionSeverity = InspectionSeverity.NORMAL
    technician_note: Optional[str] = None
    recommendation: Optional[str] = None

class AddServiceRequest(BaseModel):
    service_id: int
    quantity: float = 1.0
    discount: float = 0.0
    notes: Optional[str] = None

class AddPartRequest(BaseModel):
    part_id: int
    quantity: int = 1
    discount: float = 0.0
    notes: Optional[str] = None

def generate_ro_code(db: Session) -> str:
    today_str = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(RepairOrder).filter(RepairOrder.code.like(f"RO-{today_str}-%")).count()
    return f"RO-{today_str}-{(count + 1):04d}"

def verify_technician_access(ro: RepairOrder, current_user: User):
    """Phòng chống IDOR: KTV chỉ được cập nhật phiếu sửa chữa được giao cho chính mình"""
    if current_user.role == UserRole.TECHNICIAN:
        if ro.technician_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Quyền truy cập bị từ chối: Bạn không được phân công phụ trách phiếu sửa chữa này (IDOR Protection)."
            )

@router.post("", response_model=RepairOrderOut)
def create_repair_order(
    ro_in: RepairOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == ro_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy xe")

    if ro_in.mileage_at_reception > vehicle.current_mileage:
        vehicle.current_mileage = ro_in.mileage_at_reception

    code = generate_ro_code(db)
    repair_order = RepairOrder(
        code=code,
        customer_id=vehicle.customer_id,
        vehicle_id=ro_in.vehicle_id,
        mileage_at_reception=ro_in.mileage_at_reception,
        initial_symptoms=ro_in.initial_symptoms,
        technician_id=ro_in.technician_id,
        receptionist_id=current_user.id,
        status=RepairOrderStatus.RECEIVED
    )
    db.add(repair_order)
    db.commit()
    db.refresh(repair_order)
    return repair_order

@router.get("", response_model=List[RepairOrderOut])
def list_repair_orders(
    status: Optional[RepairOrderStatus] = None,
    vehicle_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(RepairOrder)
    if current_user.role == UserRole.TECHNICIAN:
        query = query.filter(RepairOrder.technician_id == current_user.id)
    if status:
        query = query.filter(RepairOrder.status == status)
    if vehicle_id:
        query = query.filter(RepairOrder.vehicle_id == vehicle_id)
    if search:
        query = query.join(Vehicle).filter(
            (RepairOrder.code.ilike(f"%{search}%")) |
            (Vehicle.license_plate.ilike(f"%{search}%"))
        )
    return query.order_by(RepairOrder.created_at.desc()).all()

@router.get("/{ro_id}", response_model=RepairOrderOut)
def get_repair_order(
    ro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa")
    verify_technician_access(ro, current_user)
    return ro

@router.put("/{ro_id}", response_model=RepairOrderOut)
def update_repair_order(
    ro_id: int,
    ro_update: RepairOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa")

    update_data = ro_update.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] == RepairOrderStatus.FINISHED:
        ro.completed_at = datetime.utcnow()

    for field, val in update_data.items():
        if hasattr(ro, field):
            setattr(ro, field, val)

    db.commit()
    db.refresh(ro)
    return ro

@router.patch("/{ro_id}/status")
def update_repair_order_status(
    ro_id: int,
    req: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại")
    
    verify_technician_access(ro, current_user)
    
    updated_ro = ROService.transition_status(
        db=db,
        repair_order_id=ro_id,
        new_status=req.status,
        user_id=current_user.id
    )
    return {
        "success": True,
        "message": f"Chuyển trạng thái thành công: {updated_ro.status.value}",
        "status": updated_ro.status.value
    }

@router.post("/{ro_id}/inspection")
def add_inspection_item(
    ro_id: int,
    req: InspectionItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.TECHNICIAN]))
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại")
    verify_technician_access(ro, current_user)

    inspection = Inspection(
        repair_order_id=ro.id,
        category=req.category,
        item=req.item,
        condition=req.condition,
        severity=req.severity,
        technician_note=req.technician_note,
        recommendation=req.recommendation,
        status="COMPLETED"
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return {
        "success": True,
        "message": "Đã ghi nhận kết quả chẩn đoán kỹ thuật",
        "data": {"id": inspection.id, "item": inspection.item, "severity": inspection.severity.value}
    }

@router.post("/{ro_id}/services")
def add_service_to_ro(
    ro_id: int,
    req: AddServiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST, UserRole.TECHNICIAN]))
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại")
    verify_technician_access(ro, current_user)

    service = db.query(Service).filter(Service.id == req.service_id).first()
    if not service or not service.is_active:
        raise HTTPException(status_code=404, detail="Dịch vụ không tồn tại hoặc đã ngừng cung cấp")

    subtotal = round(service.labor_cost * req.quantity - req.discount, 2)
    ro_service = RepairOrderService(
        repair_order_id=ro.id,
        service_id=service.id,
        quantity=req.quantity,
        unit_price=service.labor_cost,
        discount=req.discount,
        subtotal=max(0.0, subtotal),
        notes=req.notes
    )
    db.add(ro_service)
    
    # Also add to legacy items for backward compatibility
    item = RepairOrderItem(
        repair_order_id=ro.id,
        item_type=RepairOrderItemType.SERVICE,
        service_id=service.id,
        name=service.name,
        quantity=req.quantity,
        labor_cost=service.labor_cost,
        total_price=max(0.0, subtotal),
        notes=req.notes
    )
    db.add(item)
    
    ro.final_cost = (ro.final_cost or 0.0) + max(0.0, subtotal)
    db.commit()
    return {"success": True, "message": "Đã thêm dịch vụ vào phiếu sửa chữa"}

@router.post("/{ro_id}/parts")
def add_part_to_ro(
    ro_id: int,
    req: AddPartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST, UserRole.TECHNICIAN]))
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại")
    verify_technician_access(ro, current_user)

    part = db.query(Part).filter(Part.id == req.part_id).first()
    if not part or not part.is_active:
        raise HTTPException(status_code=404, detail="Phụ tùng không tồn tại hoặc đã ngừng kinh doanh")

    # Export part with atomic stock decrease and negative check
    tx = InventoryService.export_part_for_repair_order(
        db=db,
        part_id=part.id,
        quantity=req.quantity,
        repair_order_id=ro.id,
        user_id=current_user.id,
        notes=req.notes
    )

    subtotal = round(part.unit_price * req.quantity - req.discount, 2)
    ro_part = RepairOrderPart(
        repair_order_id=ro.id,
        part_id=part.id,
        quantity=req.quantity,
        unit_price=part.unit_price,
        discount=req.discount,
        subtotal=max(0.0, subtotal),
        notes=req.notes
    )
    db.add(ro_part)

    item = RepairOrderItem(
        repair_order_id=ro.id,
        item_type=RepairOrderItemType.PART,
        part_id=part.id,
        name=part.name,
        quantity=req.quantity,
        unit_price=part.unit_price,
        total_price=max(0.0, subtotal),
        notes=req.notes
    )
    db.add(item)

    ro.final_cost = (ro.final_cost or 0.0) + max(0.0, subtotal)
    db.commit()
    return {
        "success": True, 
        "message": "Đã xuất phụ tùng và thêm vào phiếu sửa chữa",
        "stock_remaining": tx.new_quantity
    }

@router.post("/{ro_id}/assign-technician")
def assign_technician(
    ro_id: int,
    req: AssignTechnicianRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Phiếu sửa chữa không tồn tại")

    tech = db.query(User).filter(User.id == req.technician_id, User.role == UserRole.TECHNICIAN).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Kỹ thuật viên không tồn tại hoặc tài khoản không có vai trò TECHNICIAN")

    ro.technician_id = tech.id
    if ro.status == RepairOrderStatus.RECEIVED:
        ro.status = RepairOrderStatus.INSPECTING

    db.commit()
    return {
        "success": True,
        "message": f"Đã phân công Kỹ thuật viên '{tech.full_name}' phụ trách xe."
    }

@router.post("/{ro_id}/items", response_model=RepairOrderItemOut)
def add_item_to_repair_order(
    ro_id: int,
    item_in: RepairOrderItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    if not ro:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa")

    unit_price = item_in.unit_price
    labor_cost = item_in.labor_cost
    quantity = item_in.quantity

    if item_in.item_type == RepairOrderItemType.SERVICE and item_in.service_id:
        srv = db.query(Service).filter(Service.id == item_in.service_id).first()
        if srv and labor_cost == 0:
            labor_cost = srv.labor_cost

    if item_in.item_type == RepairOrderItemType.PART and item_in.part_id:
        part = db.query(Part).filter(Part.id == item_in.part_id).first()
        if not part:
            raise HTTPException(status_code=404, detail="Không tìm thấy phụ tùng")
        if part.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail=f"Phụ tùng {part.name} không đủ tồn kho")
        if unit_price == 0:
            unit_price = part.unit_price
        part.stock_quantity -= int(quantity)

    total_price = (unit_price * quantity) + labor_cost

    item = RepairOrderItem(
        repair_order_id=ro_id,
        item_type=item_in.item_type,
        service_id=item_in.service_id,
        part_id=item_in.part_id,
        name=item_in.name,
        quantity=quantity,
        unit_price=unit_price,
        labor_cost=labor_cost,
        total_price=total_price,
        notes=item_in.notes
    )
    db.add(item)
    ro.final_cost = (ro.final_cost or 0.0) + total_price
    db.commit()
    db.refresh(item)
    return item
