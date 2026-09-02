from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Appointment, AppointmentStatus, Vehicle, User, UserRole
from backend.app.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from backend.app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])

@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    apt_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == apt_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin xe")

    # Conflict Check (TC03): Check if vehicle already has an active appointment on the same date/time (+- 60 mins)
    apt_date = apt_in.appointment_date
    window_start = apt_date - timedelta(minutes=59)
    window_end = apt_date + timedelta(minutes=59)

    conflict = db.query(Appointment).filter(
        Appointment.vehicle_id == apt_in.vehicle_id,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
        Appointment.appointment_date >= window_start,
        Appointment.appointment_date <= window_end
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Xung đột lịch hẹn: Phương tiện biển số '{vehicle.license_plate}' đã có lịch hẹn vào {conflict.appointment_date.strftime('%H:%M %d/%m/%Y')}!"
        )

    now = datetime.utcnow()
    today_str = now.strftime("%Y%m%d")
    count = db.query(Appointment).filter(Appointment.appointment_code.like(f"APT-{today_str}-%")).count()
    apt_code = f"APT-{today_str}-{(count + 1):04d}"

    data = apt_in.model_dump()
    data["appointment_code"] = apt_code
    data["customer_id"] = vehicle.customer_id

    appointment = Appointment(**data)
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

@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
    return apt

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

@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.RECEPTIONIST]))
):
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")

    apt.status = AppointmentStatus.CANCELLED
    db.commit()
    return {"success": True, "message": "Đã hủy lịch hẹn thành công"}
