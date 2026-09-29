import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models import Part, Vehicle, RepairOrder, Appointment, Customer, Invoice, InvoiceStatus, Payment

def check_inventory_tool(db: Session, part_name: str) -> str:
    """Tra cứu tồn kho phụ tùng."""
    parts = db.query(Part).filter(Part.name.ilike(f"%{part_name}%")).limit(5).all()
    if not parts:
        return f"Không tìm thấy phụ tùng nào khớp với '{part_name}'."
    
    res = []
    for p in parts:
        res.append(f"- {p.name} (Mã: {p.code}): Tồn kho {p.stock_quantity} {p.unit}, Giá: {p.unit_price:,.0f} VNĐ")
    return "\n".join(res)

def lookup_vehicle_history_tool(db: Session, license_plate: str) -> str:
    """Tra cứu lịch sử sửa chữa của xe."""
    vehicle = db.query(Vehicle).filter(Vehicle.license_plate.ilike(f"%{license_plate}%")).first()
    if not vehicle:
        return f"Không tìm thấy xe biển số {license_plate} trong hệ thống."
    
    ros = db.query(RepairOrder).filter(RepairOrder.vehicle_id == vehicle.id).order_by(RepairOrder.created_at.desc()).limit(3).all()
    if not ros:
        return f"Xe {license_plate} ({vehicle.brand} {vehicle.model}) chưa có lịch sử sửa chữa nào."
    
    res = [f"Lịch sử sửa chữa gần đây của xe {license_plate} ({vehicle.brand} {vehicle.model}):"]
    for ro in ros:
        date_str = ro.created_at.strftime("%d/%m/%Y") if ro.created_at else "Không rõ"
        res.append(f"- Ngày {date_str}: {ro.technical_diagnosis or 'Không ghi nhận chẩn đoán'} (Chi phí: {ro.final_cost:,.0f} VNĐ)")
    return "\n".join(res)

def check_repair_progress_tool(db: Session, license_plate: str) -> str:
    """Kiểm tra tiến độ sửa chữa hiện tại của xe."""
    vehicle = db.query(Vehicle).filter(Vehicle.license_plate.ilike(f"%{license_plate}%")).first()
    if not vehicle:
        return f"Không tìm thấy xe biển số {license_plate}."
    
    ro = db.query(RepairOrder).filter(
        RepairOrder.vehicle_id == vehicle.id,
        RepairOrder.status != "COMPLETED",
        RepairOrder.status != "FINISHED",
        RepairOrder.status != "CANCELLED"
    ).first()
    
    if not ro:
        return f"Xe {license_plate} hiện không có phiếu sửa chữa nào đang thực hiện."
    
    return f"Xe {license_plate} đang ở trạng thái: {ro.status.value if hasattr(ro.status, 'value') else ro.status}. Ghi chú KTV: {ro.internal_notes or 'Không có'}"

def get_appointment_schedule_tool(db: Session, date_str: str) -> str:
    """Xem danh sách lịch hẹn trong một ngày cụ thể (YYYY-MM-DD)."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Định dạng ngày không hợp lệ. Vui lòng dùng YYYY-MM-DD."
    
    from sqlalchemy import cast, Date
    appts = db.query(Appointment).filter(
        cast(Appointment.appointment_date, Date) == target_date
    ).all()
    
    if not appts:
        return f"Không có lịch hẹn nào vào ngày {date_str}."
    
    res = [f"Danh sách lịch hẹn ngày {date_str}:"]
    for appt in appts:
        vehicle = appt.vehicle
        lp = vehicle.license_plate if vehicle else "Không rõ"
        res.append(f"- {appt.start_time or 'Không rõ giờ'}: Xe {lp} - Dịch vụ: {appt.service_type or 'Bảo dưỡng'} ({appt.status.value if hasattr(appt.status, 'value') else appt.status})")
    
    return "\n".join(res)

def get_monthly_revenue_tool(db: Session, year: Optional[int] = None, month: Optional[int] = None) -> str:
    """Tổng hợp doanh thu theo hóa đơn giống Dashboard và kèm đối soát thanh toán."""
    now = datetime.utcnow()
    target_year = int(year or now.year)
    target_month = int(month or now.month)
    if target_month < 1 or target_month > 12:
        return "Tháng không hợp lệ. Vui lòng dùng giá trị từ 1 đến 12."
    if target_year < 2000 or target_year > 2100:
        return "Năm không hợp lệ."
    from calendar import monthrange
    start = datetime(target_year, target_month, 1)
    end = datetime(target_year, target_month, monthrange(target_year, target_month)[1], 23, 59, 59, 999999)
    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= start,
        Invoice.invoice_date <= end,
        Invoice.status != InvoiceStatus.CANCELLED,
    ).all()
    dashboard_revenue = sum(float(invoice.paid_amount or 0) for invoice in invoices)
    invoiced_total = sum(float(invoice.total_amount or 0) for invoice in invoices)
    paid_count = sum(invoice.status == InvoiceStatus.PAID for invoice in invoices)
    partial_count = sum(invoice.status == InvoiceStatus.PARTIAL for invoice in invoices)
    unpaid_count = sum(invoice.status == InvoiceStatus.UNPAID for invoice in invoices)
    payments = db.query(Payment).join(Invoice, Payment.invoice_id == Invoice.id).filter(
        Payment.payment_date >= start,
        Payment.payment_date <= end,
        Invoice.status != InvoiceStatus.CANCELLED,
    ).all()
    payment_total = sum(float(payment.amount or 0) for payment in payments)
    cancelled_count = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.CANCELLED,
        Invoice.invoice_date >= start,
        Invoice.invoice_date <= end,
    ).count()
    return (
        f"Doanh thu trên Dashboard theo hóa đơn tháng {target_month:02d}/{target_year}: {dashboard_revenue:,.0f} VNĐ\n"
        f"- Tổng giá trị hóa đơn: {invoiced_total:,.0f} VNĐ\n"
        f"- Số hóa đơn trong kỳ: {len(invoices)} (đã thanh toán: {paid_count}, trả một phần: {partial_count}, chưa thanh toán: {unpaid_count})\n"
        f"- Tiền thanh toán ghi nhận trong kỳ để đối soát: {payment_total:,.0f} VNĐ ({len(payments)} phiếu)\n"
        f"- Hóa đơn hủy loại khỏi doanh thu: {cancelled_count}\n"
        "- Căn cứ chính: Invoice.invoice_date và Invoice.paid_amount, cùng logic Dashboard; không dùng số liệu ước tính."
    )

# =====================================================================
# AGENT TOOL SCHEMAS FOR OPENAI / GROQ
# =====================================================================
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_inventory_tool",
            "description": "Tra cứu số lượng tồn kho và giá bán của một phụ tùng bất kỳ trong kho Garage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_name": {
                        "type": "string",
                        "description": "Tên phụ tùng cần tra cứu, ví dụ: 'Lọc nhớt', 'Má phanh', 'Bugi'"
                    }
                },
                "required": ["part_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_vehicle_history_tool",
            "description": "Tra cứu lịch sử các lần sửa chữa trước đây của một chiếc xe dựa vào biển số.",
            "parameters": {
                "type": "object",
                "properties": {
                    "license_plate": {
                        "type": "string",
                        "description": "Biển số xe cần tra cứu, ví dụ: '51G-12345'"
                    }
                },
                "required": ["license_plate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_repair_progress_tool",
            "description": "Kiểm tra tiến độ sửa chữa hiện tại (đang nằm ở bước nào, trạng thái gì) của một chiếc xe tại Garage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "license_plate": {
                        "type": "string",
                        "description": "Biển số xe cần kiểm tra tiến độ, ví dụ: '51G-12345'"
                    }
                },
                "required": ["license_plate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_appointment_schedule_tool",
            "description": "Lấy danh sách các lịch hẹn sửa chữa, bảo dưỡng của Garage trong một ngày cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "Ngày cần xem lịch hẹn định dạng YYYY-MM-DD, ví dụ: '2026-10-25'"
                    }
                },
                "required": ["date_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_revenue_tool",
            "description": "Tra cứu doanh thu thực thu của tháng từ các thanh toán đã ghi nhận trong CSDL; loại trừ hóa đơn đã hủy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Năm cần tra cứu; bỏ trống để dùng năm hiện tại."},
                    "month": {"type": "integer", "description": "Tháng cần tra cứu 1-12; bỏ trống để dùng tháng hiện tại."}
                },
                "required": []
            }
        }
    }
]

# =====================================================================
# DISPATCHER
# =====================================================================
def execute_tool(db: Session, tool_name: str, kwargs: Dict[str, Any]) -> str:
    """Gọi hàm tương ứng dựa trên tên tool do LLM trả về."""
    if tool_name == "check_inventory_tool":
        return check_inventory_tool(db, kwargs.get("part_name", ""))
    elif tool_name == "lookup_vehicle_history_tool":
        return lookup_vehicle_history_tool(db, kwargs.get("license_plate", ""))
    elif tool_name == "check_repair_progress_tool":
        return check_repair_progress_tool(db, kwargs.get("license_plate", ""))
    elif tool_name == "get_appointment_schedule_tool":
        return get_appointment_schedule_tool(db, kwargs.get("date_str", ""))
    elif tool_name == "get_monthly_revenue_tool":
        return get_monthly_revenue_tool(db, kwargs.get("year"), kwargs.get("month"))
    else:
        return f"Lỗi: Không tìm thấy công cụ {tool_name}"
