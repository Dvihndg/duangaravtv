from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Customer, Vehicle, RepairOrder, User, UserRole
from backend.app.schemas import CustomerCreate, CustomerOut, VehicleCreate, VehicleOut
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/v1", tags=["Customers & Vehicles"])

# Customer endpoints
@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Customer).filter(Customer.phone == customer_in.phone.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Số điện thoại khách hàng đã tồn tại trên hệ thống")

    count = db.query(Customer).count()
    code = f"CUS-{datetime.utcnow().year}-{(count + 1):06d}"

    data = customer_in.model_dump()
    customer = Customer(
        customer_code=code,
        full_name=data["full_name"],
        phone=data["phone"].strip(),
        email=data.get("email"),
        address=data.get("address"),
        status="ACTIVE"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/customers", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc SĐT"),
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Customer)
    if not include_deleted:
        query = query.filter(Customer.deleted_at.is_(None))
    if search:
        query = query.filter(
            (Customer.full_name.ilike(f"%{search}%")) | (Customer.phone.ilike(f"%{search}%"))
        )
    return query.order_by(Customer.created_at.desc()).all()

@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin khách hàng")
    return customer

@router.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin khách hàng")

    customer.full_name = customer_in.full_name
    customer.phone = customer_in.phone.strip()
    customer.email = customer_in.email
    customer.address = customer_in.address
    db.commit()
    db.refresh(customer)
    return customer

@router.delete("/customers/{customer_id}")
def soft_delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER]))
):
    """Xóa mềm khách hàng (Soft delete) - bảo toàn 100% hồ sơ xe và lịch sử sửa chữa"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin khách hàng")

    customer.deleted_at = datetime.utcnow()
    customer.status = "INACTIVE"
    db.commit()
    return {
        "success": True, 
        "message": f"Đã xóa mềm khách hàng #{customer_id}. Toàn bộ lịch sử bảo dưỡng và hồ sơ xe được bảo lưu an toàn."
    }

# Vehicle endpoints
@router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_in: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    license_plate = vehicle_in.license_plate.upper().strip()
    existing = db.query(Vehicle).filter(Vehicle.license_plate == license_plate).first()
    if existing:
        raise HTTPException(status_code=400, detail="Biển số xe đã được đăng ký trong hệ thống")

    if not vehicle_in.customer_id:
        raise HTTPException(status_code=400, detail="Vui lòng chỉ định customer_id sở hữu xe")

    vehicle_data = vehicle_in.model_dump()
    vehicle_data["license_plate"] = license_plate
    vehicle = Vehicle(**vehicle_data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.get("/vehicles", response_model=List[VehicleOut])
def list_vehicles(
    search: Optional[str] = Query(None, description="Tìm theo biển số xe hoặc thương hiệu"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Vehicle)
    if search:
        query = query.filter(
            (Vehicle.license_plate.ilike(f"%{search}%")) |
            (Vehicle.brand.ilike(f"%{search}%")) |
            (Vehicle.model.ilike(f"%{search}%"))
        )
    return query.all()

@router.get("/vehicles/{vehicle_id}/history")
def get_vehicle_repair_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy phương tiện")

    ros = db.query(RepairOrder).filter(RepairOrder.vehicle_id == vehicle.id).order_by(RepairOrder.created_at.desc()).all()
    history_records = []
    for ro in ros:
        history_records.append({
            "repair_order_id": ro.id,
            "repair_order_code": ro.code,
            "date": ro.created_at.strftime("%d/%m/%Y") if ro.created_at else "",
            "mileage": ro.mileage_at_reception or ro.mileage_in,
            "complaint": ro.customer_complaint or ro.initial_symptoms,
            "diagnosis": ro.technical_diagnosis,
            "status": ro.status.value if hasattr(ro.status, 'value') else str(ro.status),
            "cost": ro.final_cost or ro.estimated_cost,
            "technician_name": ro.technician.full_name if ro.technician else "Chưa phân công",
            "services": [s.name for s in ro.items if s.item_type.value == "service"] if ro.items else [],
            "parts": [p.name for p in ro.items if p.item_type.value == "part"] if ro.items else []
        })

    return {
        "vehicle": {
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "current_mileage": vehicle.current_mileage
        },
        "total_visits": len(history_records),
        "history": history_records
    }
