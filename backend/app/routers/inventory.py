from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Service, Part, User, UserRole
from backend.app.schemas import ServiceCreate, ServiceOut, PartCreate, PartOut
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/v1", tags=["Services & Spare Parts Inventory"])

# Services
@router.post("/services", response_model=ServiceOut)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    existing = db.query(Service).filter(Service.code == service_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã dịch vụ đã tồn tại")

    service = Service(**service_in.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.get("/services", response_model=List[ServiceOut])
def list_services(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Service).filter(Service.is_active == True)
    if search:
        query = query.filter(
            (Service.name.ilike(f"%{search}%")) | (Service.code.ilike(f"%{search}%"))
        )
    return query.all()

# Spare Parts
@router.post("/parts", response_model=PartOut)
def create_part(
    part_in: PartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER]))
):
    existing = db.query(Part).filter(Part.code == part_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã phụ tùng đã tồn tại")

    part = Part(**part_in.model_dump())
    db.add(part)
    db.commit()
    db.refresh(part)
    return part

@router.get("/parts", response_model=List[PartOut])
def list_parts(
    search: Optional[str] = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Part).filter(Part.is_active == True)
    if low_stock_only:
        query = query.filter(Part.stock_quantity <= Part.min_stock_alert)
    if search:
        query = query.filter(
            (Part.name.ilike(f"%{search}%")) | (Part.code.ilike(f"%{search}%"))
        )
    return query.all()
