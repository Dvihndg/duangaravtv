from typing import List, Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Appointment, AppointmentStatus, Vehicle, User, UserRole
from backend.app.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])

@router.post("", response_model=AppointmentOut)
def create_appointment(
    apt_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == apt_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin xe")

    appointment = Appointment(**apt_in.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    status: Optional[AppointmentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Appointment)
    if status:
        query = query.filter(Appointment.status == status)
    return query.order_by(Appointment.appointment_date.asc()).all()

@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int,
    apt_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")

    update_data = apt_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(apt, field, val)

    db.commit()
    db.refresh(apt)
    return apt
