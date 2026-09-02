from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    VehicleReception, Vehicle, Customer, Appointment, RepairOrder, 
    RepairOrderStatus, User, UserRole
)
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/receptions", tags=["Vehicle Reception"])

class CreateReceptionRequest(BaseModel):
    vehicle_id: int
    customer_id: Optional[int] = None
    appointment_id: Optional[int] = None
    mileage: int
    fuel_level: str = "1/2"
    exterior_condition: Optional[str] = None
    interior_condition: Optional[str] = None
    existing_damage: Optional[str] = None
    customer_complaint: str
    requested_services: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
def list_receptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(VehicleReception).order_by(VehicleReception.id.desc()).all()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_vehicle_reception(
    req: CreateReceptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == req.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Phương tiện không tồn tại.")

    customer_id = req.customer_id or vehicle.customer_id
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại.")

    now = datetime.utcnow()
    today_str = now.strftime("%Y%m%d")
    
    # Generate reception code: REC-YYYYMMDD-XXXX
    count_today = db.query(VehicleReception).filter(VehicleReception.reception_code.like(f"REC-{today_str}-%")).count()
    rec_code = f"REC-{today_str}-{count_today + 1:04d}"

    # Update vehicle mileage if higher
    if req.mileage > vehicle.current_mileage:
        vehicle.current_mileage = req.mileage

    reception = VehicleReception(
        reception_code=rec_code,
        customer_id=customer.id,
        vehicle_id=vehicle.id,
        appointment_id=req.appointment_id,
        mileage=req.mileage,
        fuel_level=req.fuel_level,
        exterior_condition=req.exterior_condition,
        interior_condition=req.interior_condition,
        existing_damage=req.existing_damage,
        customer_complaint=req.customer_complaint,
        requested_services=req.requested_services,
        notes=req.notes,
        received_by_id=current_user.id,
        received_at=now
    )
    db.add(reception)
    db.flush()

    # Automatically create linked RepairOrder
    ro_count = db.query(RepairOrder).filter(RepairOrder.code.like(f"RO-{today_str}-%")).count()
    ro_code = f"RO-{today_str}-{ro_count + 1:04d}"

    new_ro = RepairOrder(
        code=ro_code,
        customer_id=customer.id,
        vehicle_id=vehicle.id,
        appointment_id=req.appointment_id,
        reception_id=reception.id,
        receptionist_id=current_user.id,
        mileage_in=req.mileage,
        mileage_at_reception=req.mileage,
        customer_complaint=req.customer_complaint,
        initial_symptoms=req.customer_complaint,
        status=RepairOrderStatus.RECEIVED,
        created_at=now
    )
    db.add(new_ro)
    db.commit()
    db.refresh(reception)
    db.refresh(new_ro)

    return {
        "success": True,
        "message": "Tiếp nhận xe thành công và đã tạo Phiếu sửa chữa mới.",
        "data": {
            "reception_id": reception.id,
            "reception_code": reception.reception_code,
            "repair_order_id": new_ro.id,
            "repair_order_code": new_ro.code,
            "vehicle_plate": vehicle.license_plate,
            "customer_name": customer.full_name
        }
    }

@router.get("/{id}")
def get_reception_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(VehicleReception).filter(VehicleReception.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Biên bản tiếp nhận không tồn tại.")
    return rec
