import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models import Part, Vehicle, RepairOrder, Appointment, Customer

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
    else:
        return f"Lỗi: Không tìm thấy công cụ {tool_name}"
