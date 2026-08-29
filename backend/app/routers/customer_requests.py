import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.app.database import get_db
from backend.app.models import (
    CustomerRequest, CustomerRequestStatus, Customer, Vehicle, User, UserRole
)
from backend.app.schemas.customer_request import (
    CustomerRequestCreate, CustomerRequestUpdateStatus,
    CustomerRequestAssign, CustomerRequestAddNote, CustomerRequestResponse
)
from backend.app.routers.auth import get_current_user

router = APIRouter(prefix="/customer-requests", tags=["Customer Requests"])

# Global memory queue for Server-Sent Events (SSE) Real-time notifications
sse_clients: List[asyncio.Queue] = []

async def notify_admin_clients(data: dict):
    """Broadcasting real-time event to all connected Admin SSE clients"""
    for queue in list(sse_clients):
        try:
            await queue.put(data)
        except Exception:
            if queue in sse_clients:
                sse_clients.remove(queue)


def generate_request_code(db: Session) -> str:
    """Tự động sinh mã yêu cầu định dạng REQ-YYYYMMDD-XXXX"""
    today_str = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"REQ-{today_str}-"
    
    last_req = db.query(CustomerRequest).filter(
        CustomerRequest.request_code.like(f"{prefix}%")
    ).order_by(desc(CustomerRequest.id)).first()

    if last_req:
        try:
            last_seq = int(last_req.request_code.split("-")[-1])
            new_seq = last_seq + 1
        except ValueError:
            new_seq = 1
    else:
        new_seq = 1

    return f"{prefix}{new_seq:04d}"


def map_to_response(req: CustomerRequest) -> dict:
    assigned_name = None
    if req.assigned_employee:
        assigned_name = req.assigned_employee.full_name

    return {
        "id": req.id,
        "requestCode": req.request_code,
        "fullName": req.full_name,
        "phone": req.phone,
        "email": req.email,
        "address": req.address,
        "licensePlate": req.license_plate,
        "vehicleBrand": req.vehicle_brand,
        "vehicleModel": req.vehicle_model,
        "manufactureYear": req.manufacture_year,
        "currentMileage": req.current_mileage,
        "serviceType": req.service_type,
        "description": req.description,
        "preferredDate": req.preferred_date,
        "preferredTime": req.preferred_time,
        "note": req.note,
        "status": req.status,
        "adminNote": req.admin_note,
        "assignedEmployeeId": req.assigned_employee_id,
        "assignedEmployeeName": assigned_name,
        "customerId": req.customer_id,
        "vehicleId": req.vehicle_id,
        "createdAt": req.created_at,
        "updatedAt": req.updated_at
    }


# 1. PUBLIC: POST /api/v1/customer-requests (Gửi Yêu Cầu Dịch Vụ)
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer_request(payload: CustomerRequestCreate, db: Session = Depends(get_db)):
    # Anti-Spam Guard: Chống gửi trùng lặp trong vòng 60 giây cùng SĐT & Biển số
    one_min_ago = datetime.utcnow() - timedelta(seconds=60)
    recent_spam = db.query(CustomerRequest).filter(
        CustomerRequest.phone == payload.phone,
        CustomerRequest.license_plate == payload.licensePlate,
        CustomerRequest.created_at >= one_min_ago
    ).first()

    if recent_spam:
        raise HTTPException(
            status_code=429,
            detail=f"Yêu cầu của bạn đã được tiếp nhận trước đó (Mã: {recent_spam.request_code}). Vui lòng đợi trong giây lát!"
        )

    # Section 23: Tự động nhận diện Khách Hàng cũ / tạo Khách Hàng mới
    customer = db.query(Customer).filter(Customer.phone == payload.phone).first()
    if not customer:
        customer = Customer(
            full_name=payload.fullName,
            phone=payload.phone,
            email=payload.email,
            address=payload.address
        )
        db.add(customer)
        db.flush()

    # Section 24: Tự động nhận diện Xe cũ / tạo Xe mới
    vehicle = db.query(Vehicle).filter(Vehicle.license_plate == payload.licensePlate).first()
    if not vehicle:
        vehicle = Vehicle(
            license_plate=payload.licensePlate,
            brand=payload.vehicleBrand,
            model=payload.vehicleModel,
            year=payload.manufactureYear or 2022,
            current_mileage=payload.currentMileage or 0,
            customer_id=customer.id
        )
        db.add(vehicle)
        db.flush()
    else:
        # Cập nhật số km mới nhất nếu có
        if payload.currentMileage and payload.currentMileage > vehicle.current_mileage:
            vehicle.current_mileage = payload.currentMileage

    # Sinh mã yêu cầu dạng REQ-YYYYMMDD-XXXX
    req_code = generate_request_code(db)

    # Tạo bản ghi CustomerRequest chính thức
    new_request = CustomerRequest(
        request_code=req_code,
        full_name=payload.fullName,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        license_plate=payload.licensePlate,
        vehicle_brand=payload.vehicleBrand,
        vehicle_model=payload.vehicleModel,
        manufacture_year=payload.manufactureYear,
        current_mileage=payload.currentMileage or 0,
        service_type=payload.serviceType,
        description=payload.description,
        preferred_date=payload.preferredDate,
        preferred_time=payload.preferredTime,
        note=payload.note,
        status=CustomerRequestStatus.PENDING,
        customer_id=customer.id,
        vehicle_id=vehicle.id
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    res_data = map_to_response(new_request)

    # Phát thông báo Real-time SSE cho tất cả Admin đang kết nối
    asyncio.create_task(notify_admin_clients({
        "event": "NEW_CUSTOMER_REQUEST",
        "data": res_data
    }))

    return res_data


# 2. REALTIME SSE: GET /api/v1/customer-requests/stream (Lắng Nghe Thông Báo Realtime)
@router.get("/stream")
async def stream_customer_requests():
    async def event_generator():
        client_queue = asyncio.Queue()
        sse_clients.append(client_queue)
        try:
            while True:
                data = await client_queue.get()
                import json
                yield f"event: message\ndata: {json.dumps(data, default=str)}\n\n"
        except asyncio.CancelledError:
            if client_queue in sse_clients:
                sse_clients.remove(client_queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# 3. PUBLIC: GET /api/v1/customer-requests/code/{requestCode} (Tra Cứu Trạng Thái Cho Khách Hàng)
@router.get("/code/{request_code}")
def get_request_by_code(request_code: str, db: Session = Depends(get_db)):
    req = db.query(CustomerRequest).filter(
        CustomerRequest.request_code == request_code.strip().upper()
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy mã yêu cầu này trên hệ thống!")

    return map_to_response(req)


# 4. ADMIN/MANAGER: GET /api/v1/customer-requests (Xem Danh Sách Yêu Cầu)
@router.get("")
def list_customer_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    service_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CustomerRequest)

    if status_filter:
        query = query.filter(CustomerRequest.status == status_filter)

    if service_type:
        query = query.filter(CustomerRequest.service_type == service_type)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                CustomerRequest.request_code.like(s),
                CustomerRequest.full_name.like(s),
                CustomerRequest.phone.like(s),
                CustomerRequest.license_plate.like(s),
                CustomerRequest.email.like(s)
            )
        )

    requests = query.order_by(desc(CustomerRequest.created_at)).all()
    return [map_to_response(r) for r in requests]


# 5. ADMIN/MANAGER: GET /api/v1/customer-requests/{id} (Chi Tiết Yêu Cầu)
@router.get("/{req_id}")
def get_customer_request_detail(req_id: int, db: Session = Depends(get_db)):
    req = db.query(CustomerRequest).filter(CustomerRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu dịch vụ!")
    return map_to_response(req)


# 6. ADMIN/MANAGER: PATCH /api/v1/customer-requests/{id}/status (Cập Nhật Trạng Thái)
@router.patch("/{req_id}/status")
async def update_request_status(
    req_id: int,
    payload: CustomerRequestUpdateStatus,
    db: Session = Depends(get_db)
):
    req = db.query(CustomerRequest).filter(CustomerRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu dịch vụ!")

    req.status = payload.status
    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    res_data = map_to_response(req)

    # Thông báo Real-time cập nhật trạng thái
    asyncio.create_task(notify_admin_clients({
        "event": "UPDATE_CUSTOMER_REQUEST",
        "data": res_data
    }))

    return res_data


# 7. ADMIN/MANAGER: POST /api/v1/customer-requests/{id}/assign (Phân Công Nhân Viên)
@router.post("/{req_id}/assign")
async def assign_employee(
    req_id: int,
    payload: CustomerRequestAssign,
    db: Session = Depends(get_db)
):
    req = db.query(CustomerRequest).filter(CustomerRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu dịch vụ!")

    if payload.assigned_employee_id:
        emp = db.query(User).filter(User.id == payload.assigned_employee_id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên này!")
        req.assigned_employee_id = emp.id
    else:
        req.assigned_employee_id = None

    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    res_data = map_to_response(req)
    asyncio.create_task(notify_admin_clients({
        "event": "UPDATE_CUSTOMER_REQUEST",
        "data": res_data
    }))

    return res_data


# 8. ADMIN/MANAGER: POST /api/v1/customer-requests/{id}/note (Ghi Chú Admin)
@router.post("/{req_id}/note")
async def add_admin_note(
    req_id: int,
    payload: CustomerRequestAddNote,
    db: Session = Depends(get_db)
):
    req = db.query(CustomerRequest).filter(CustomerRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu dịch vụ!")

    req.admin_note = payload.admin_note
    req.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(req)

    res_data = map_to_response(req)
    asyncio.create_task(notify_admin_clients({
        "event": "UPDATE_CUSTOMER_REQUEST",
        "data": res_data
    }))

    return res_data


# 9. ADMIN: DELETE /api/v1/customer-requests/{id} (Xóa Yêu Cầu)
@router.delete("/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_request(req_id: int, db: Session = Depends(get_db)):
    req = db.query(CustomerRequest).filter(CustomerRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu dịch vụ!")

    db.delete(req)
    db.commit()
    return None
