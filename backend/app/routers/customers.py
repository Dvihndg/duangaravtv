from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Customer, Vehicle, User
from backend.app.schemas import CustomerCreate, CustomerOut, VehicleCreate, VehicleOut
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Customers & Vehicles"])

# Customer endpoints
@router.post("/customers", response_model=CustomerOut)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Customer).filter(Customer.phone == customer_in.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Số điện thoại khách hàng đã tồn tại trên hệ thống")

    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/customers", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc SĐT"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Customer)
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

# Vehicle endpoints
@router.post("/vehicles", response_model=VehicleOut)
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

@router.get("/vehicles/search/{license_plate}", response_model=VehicleOut)
def search_vehicle_by_plate(
    license_plate: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plate = license_plate.upper().strip()
    vehicle = db.query(Vehicle).filter(Vehicle.license_plate == plate).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy xe biển số {plate}")
    return vehicle
