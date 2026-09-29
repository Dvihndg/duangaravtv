"""Deterministic operational lookups used as AI context."""
from __future__ import annotations

import re
from datetime import datetime, time
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models import Appointment, Customer, Invoice, Part, RepairOrder, User, Vehicle
from backend.app.services.reporting_service import LOCAL_TZ, parse_report_period


def _money(value) -> str:
    return f"{float(value or 0):,.0f} VNĐ"


def _date(value) -> str:
    return value.strftime("%d/%m/%Y") if value else "Chưa ghi nhận"


def lookup_operational_context(db: Session, question: str) -> Optional[str]:
    text = (question or "").strip()
    lower = text.lower()
    code = re.search(r"\b(?:ro|inv|hd|ord|don)\s*[-#]?\s*[a-z0-9-]+", lower)
    if code and ("đơn" in lower or "order" in lower or "hóa đơn" in lower or "hoa don" in lower or code.group(0).startswith(("ro", "inv", "hd"))):
        return lookup_order_or_invoice(db, code.group(0).replace(" ", ""))

    if any(term in lower for term in ("tồn kho", "ton kho", "phụ tùng", "phu tung", "còn hàng", "con hang", "nhập gấp")):
        stop = {"tra", "cứu", "cho", "tôi", "kho", "tồn", "phụ", "tùng", "còn", "hàng", "nhập", "gấp", "nào", "hiện", "tại"}
        words = [word for word in re.findall(r"[\wÀ-ỹ-]+", lower) if word not in stop]
        return lookup_inventory(db, " ".join(words))

    if any(term in lower for term in ("lịch hẹn", "lich hen", "cuộc hẹn", "cuoc hen")):
        return lookup_appointments(db, text)

    if any(term in lower for term in ("khách hàng", "khach hang", "thông tin khách", "thong tin khach")):
        query = re.sub(r".*?(?:khách hàng|khach hang|thông tin khách|thong tin khach)\s*", "", text, flags=re.I).strip(" :#")
        return lookup_customer(db, query)

    return None


def lookup_order_or_invoice(db: Session, identifier: str) -> str:
    normalized = identifier.strip().upper().replace(" ", "")
    ro = db.query(RepairOrder).filter(RepairOrder.code.ilike(normalized)).first()
    invoice = None
    if normalized.startswith(("INV", "HD")):
        invoice = db.query(Invoice).filter(Invoice.invoice_number.ilike(normalized)).first()
        ro = invoice.repair_order if invoice else None
    if not ro and not invoice:
        invoice = db.query(Invoice).filter(Invoice.invoice_number.ilike(f"%{normalized}%")).first()
        ro = invoice.repair_order if invoice else None
    if not ro and normalized.startswith("RO"):
        return f"Không tìm thấy đơn hàng {identifier} trong hệ thống."
    if not ro:
        return f"Không tìm thấy hóa đơn/đơn hàng {identifier} trong hệ thống."
    invoice = invoice or ro.invoice
    vehicle = ro.vehicle
    technician = ro.technician.full_name if ro.technician else "Chưa phân công"
    status = getattr(ro.status, "value", ro.status) or "Chưa ghi nhận"
    lines = [
        "--- TRA CỨU HÓA ĐƠN / ĐƠN HÀNG ---",
        f"Mã đơn: {ro.code} | Trạng thái: {status}",
        f"Xe: {(vehicle.brand + ' ' + vehicle.model) if vehicle else 'Chưa ghi nhận'} | Biển số: {vehicle.license_plate if vehicle else 'Chưa ghi nhận'}",
        f"KTV phụ trách: {technician}",
        f"Khách hàng: {ro.customer.full_name if ro.customer else 'Chưa ghi nhận'}",
        f"Tổng tiền: {_money(invoice.total_amount if invoice else ro.final_cost)} | Đã thu: {_money(invoice.paid_amount if invoice else 0)}",
        f"Ngày tạo đơn: {_date(ro.created_at)} | Hóa đơn: {invoice.invoice_number if invoice else 'Chưa phát hành'}",
    ]
    return "\n".join(lines)


def lookup_inventory(db: Session, query: str = "") -> str:
    parts_query = db.query(Part).filter(Part.is_active == True)
    if query:
        like = f"%{query}%"
        parts_query = parts_query.filter(or_(Part.name.ilike(like), Part.code.ilike(like), Part.brand.ilike(like), Part.category.ilike(like)))
    parts = parts_query.order_by(Part.stock_quantity.asc()).limit(20).all()
    if not parts:
        return f"Không tìm thấy phụ tùng phù hợp với '{query}'."
    lines = ["--- TRA CỨU TỒN KHO ---"]
    for part in parts:
        alert = " [CẦN NHẬP GẤP]" if (part.stock_quantity or 0) < (part.min_stock_alert or 0) else ""
        lines.append(f"{part.code} | {part.name} | Tồn: {part.stock_quantity} {part.unit} | Tối thiểu: {part.min_stock_alert} | Giá: {_money(part.unit_price)}{alert}")
    return "\n".join(lines)


def lookup_appointments(db: Session, question: str) -> str:
    try:
        period = parse_report_period(question)
        start = period.start_utc
        end = period.end_utc
    except ValueError:
        now = datetime.now(LOCAL_TZ).replace(tzinfo=None)
        start, end = now.replace(hour=0, minute=0, second=0, microsecond=0), now.replace(hour=23, minute=59, second=59, microsecond=999999)
    appointments = db.query(Appointment).filter(Appointment.appointment_date >= start, Appointment.appointment_date <= end).order_by(Appointment.appointment_date).limit(50).all()
    if not appointments:
        return f"Không có lịch hẹn trong kỳ {start:%d/%m/%Y}–{end:%d/%m/%Y}."
    lines = [f"--- LỊCH HẸN {start:%d/%m/%Y}–{end:%d/%m/%Y} ---"]
    for appointment in appointments:
        vehicle = appointment.vehicle
        status = getattr(appointment.status, "value", appointment.status)
        lines.append(f"{appointment.appointment_code or appointment.id} | {appointment.appointment_date:%d/%m/%Y} {appointment.start_time or ''} | {vehicle.license_plate if vehicle else 'Chưa rõ'} | {appointment.service_type or 'Chưa ghi nhận'} | {status}")
    return "\n".join(lines)


def lookup_customer(db: Session, query: str) -> str:
    if not query:
        return "Vui lòng cung cấp tên, số điện thoại, mã khách hàng hoặc biển số để tra cứu khách hàng."
    like = f"%{query}%"
    customer = db.query(Customer).filter(or_(Customer.full_name.ilike(like), Customer.phone.ilike(like), Customer.customer_code.ilike(like))).first()
    if not customer:
        vehicle = db.query(Vehicle).filter(Vehicle.license_plate.ilike(like)).first()
        customer = vehicle.owner if vehicle else None
    if not customer:
        return f"Không tìm thấy khách hàng phù hợp với '{query}'."
    vehicles = ", ".join(f"{v.license_plate} ({v.brand} {v.model})" for v in customer.vehicles) or "Chưa đăng ký xe"
    return "\n".join([
        "--- TRA CỨU KHÁCH HÀNG ---",
        f"Mã: {customer.customer_code or 'Chưa có'} | Họ tên: {customer.full_name}",
        f"Điện thoại: {customer.phone} | Email: {customer.email or 'Chưa có'}",
        f"Địa chỉ: {customer.address or 'Chưa có'} | Trạng thái: {customer.status or 'ACTIVE'}",
        f"Xe đăng ký: {vehicles}",
    ])
