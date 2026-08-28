from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    RepairOrder, RepairOrderStatus, RepairOrderItem, RepairOrderItemType,
    Vehicle, Service, Part, User, UserRole, Invoice, InvoiceStatus
)
from backend.app.schemas import (
    RepairOrderCreate, RepairOrderUpdate, RepairOrderOut,
    RepairOrderItemCreate, RepairOrderItemOut
)
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/repair-orders", tags=["Repair Orders"])

def generate_ro_code(db: Session) -> str:
    today_str = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(RepairOrder).filter(RepairOrder.code.like(f"RO-{today_str}-%")).count()
    return f"RO-{today_str}-{(count + 1):03d}"

@router.post("", response_model=RepairOrderOut)
def create_repair_order(
    ro_in: RepairOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == ro_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy xe")

    # Update vehicle mileage
    if ro_in.mileage_at_reception > vehicle.current_mileage:
        vehicle.current_mileage = ro_in.mileage_at_reception

    code = generate_ro_code(db)
    repair_order = RepairOrder(
        code=code,
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
    
    # Handle status transition to FINISHED
    if "status" in update_data and update_data["status"] == RepairOrderStatus.FINISHED:
        ro.completed_at = datetime.utcnow()

    for field, val in update_data.items():
        setattr(ro, field, val)

    db.commit()
    db.refresh(ro)
    return ro

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

    # If linked to Service
    if item_in.item_type == RepairOrderItemType.SERVICE and item_in.service_id:
        srv = db.query(Service).filter(Service.id == item_in.service_id).first()
        if srv and labor_cost == 0:
            labor_cost = srv.labor_cost

    # If linked to Part
    if item_in.item_type == RepairOrderItemType.PART and item_in.part_id:
        part = db.query(Part).filter(Part.id == item_in.part_id).first()
        if not part:
            raise HTTPException(status_code=404, detail="Không tìm thấy phụ tùng")
        if part.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail=f"Phụ tùng {part.name} không đủ tồn kho (Còn {part.stock_quantity})")
        if unit_price == 0:
            unit_price = part.unit_price
        
        # Deduct stock
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

    # Recalculate repair order total
    ro.final_cost = sum([i.total_price for i in ro.items]) + total_price

    db.commit()
    db.refresh(item)
    return item

@router.delete("/{ro_id}/items/{item_id}")
def delete_repair_order_item(
    ro_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(RepairOrderItem).filter(
        RepairOrderItem.id == item_id, RepairOrderItem.repair_order_id == ro_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy hạng mục trong phiếu")

    # Restore stock if part
    if item.item_type == RepairOrderItemType.PART and item.part_id:
        part = db.query(Part).filter(Part.id == item.part_id).first()
        if part:
            part.stock_quantity += int(item.quantity)

    ro = db.query(RepairOrder).filter(RepairOrder.id == ro_id).first()
    db.delete(item)
    db.commit()

    # Recalculate cost
    ro.final_cost = sum([i.total_price for i in ro.items])
    db.commit()

    return {"message": "Đã xóa hạng mục thành công"}
