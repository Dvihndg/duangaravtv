# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
import math
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import (
    Customer, Vehicle, Appointment, RepairOrder, RepairOrderStatus,
    Invoice, InvoiceStatus, Part, Service, RepairOrderItem, CustomerRequest
)
from backend.app.auth import get_current_user

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Reporting"])

@router.get("/dashboard")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total_customers = db.query(Customer).count()
    total_vehicles = db.query(Vehicle).count()
    active_repair_orders = db.query(RepairOrder).filter(
        RepairOrder.status.in_([
            RepairOrderStatus.RECEIVED,
            RepairOrderStatus.INSPECTING,
            RepairOrderStatus.QUOTATION_PENDING,
            RepairOrderStatus.WAITING_CUSTOMER_APPROVAL,
            RepairOrderStatus.APPROVED,
            RepairOrderStatus.IN_REPAIR,
            RepairOrderStatus.WAITING_PARTS
        ])
    ).count()

    pending_appointments = db.query(Appointment).filter(
        Appointment.status == "pending"
    ).count()

    total_revenue = db.query(func.sum(Invoice.paid_amount)).scalar() or 0.0
    unpaid_invoices_count = db.query(Invoice).filter(Invoice.status == InvoiceStatus.UNPAID).count()
    low_stock_parts_count = db.query(Part).filter(Part.stock_quantity <= Part.min_stock_alert).count()

    # Top popular services
    top_items = (
        db.query(
            RepairOrderItem.name,
            func.count(RepairOrderItem.id).label("usage_count"),
            func.sum(RepairOrderItem.total_price).label("total_sales")
        )
        .group_by(RepairOrderItem.name)
        .order_by(func.count(RepairOrderItem.id).desc())
        .limit(5)
        .all()
    )

    top_services_data = [
        {"name": item[0], "count": item[1], "revenue": item[2] or 0.0}
        for item in top_items
    ]

    from datetime import datetime, timezone
    import calendar

    def minutes_ago(created_at):
        """Handle both SQLite naive and PostgreSQL timezone-aware datetimes."""
        if not created_at:
            return 0
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return max(0, math.floor(
            (datetime.now(timezone.utc) - created_at).total_seconds() / 60
        ))

    # Prepare last 6 months revenue data
    # Fallback if dateutil is not available (it's not in requirements)
    six_months_revenue = []
    today = datetime.now(timezone.utc)
    # Go back 5 months
    start_month = today.month - 5
    start_year = today.year
    if start_month <= 0:
        start_month += 12
        start_year -= 1
        
    start_date = datetime(start_year, start_month, 1)

    # Group revenue by month
    # We fetch all paid invoices from start_date
    recent_invoices = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.PAID,
        Invoice.invoice_date >= start_date
    ).all()

    revenue_by_month = {}
    for inv in recent_invoices:
        m_key = f"T{inv.invoice_date.month}"
        revenue_by_month[m_key] = revenue_by_month.get(m_key, 0) + (inv.paid_amount or 0)

    # Construct the array
    # Iterate through the last 6 months to ensure chronological order
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        m_key = f"T{m}"
        six_months_revenue.append({
            "month": m_key,
            "revenue": revenue_by_month.get(m_key, 0)
        })

    # Fetch recent activities
    recent_activities = []
    
    recent_requests = db.query(CustomerRequest).order_by(CustomerRequest.created_at.desc()).limit(5).all()
    recent_orders = db.query(RepairOrder).order_by(RepairOrder.created_at.desc()).limit(5).all()
    
    for req in recent_requests:
        ago = minutes_ago(req.created_at)
        recent_activities.append({
            "type": "request",
            "time_ago_mins": max(0, ago),
            "created_at": req.created_at,
            "title": f"YÃƒÂªu cÃ¡ÂºÂ§u tÃ¡Â»Â« {req.full_name}",
            "description": f"Xe {req.license_plate} - {req.service_type or 'BÃ¡ÂºÂ£o dÃ†Â°Ã¡Â»Â¡ng'}",
            "icon": "fa-bell",
            "color": "#fbbf24"
        })
        
    for ro in recent_orders:
        ago = minutes_ago(ro.created_at)
        vehicle = getattr(ro, "vehicle", None)
        recent_activities.append({
            "type": "order",
            "time_ago_mins": max(0, ago),
            "created_at": ro.created_at,
            "title": f"LÃ¡ÂºÂ­p phiÃ¡ÂºÂ¿u sÃ¡Â»Â­a chÃ¡Â»Â¯a {ro.code}",
            "description": f"Xe {getattr(vehicle, 'license_plate', None) or 'N/A'}",
            "icon": "fa-wrench",
            "color": "#38bdf8"
        })
        
    # Sort combined activities by created_at desc
    recent_activities.sort(key=lambda x: x["created_at"], reverse=True)
    # Take top 5
    recent_activities = recent_activities[:5]

    return {
        "kpi": {
            "total_customers": total_customers,
            "total_vehicles": total_vehicles,
            "active_repair_orders": active_repair_orders,
            "pending_appointments": pending_appointments,
            "total_revenue": total_revenue,
            "unpaid_invoices_count": unpaid_invoices_count,
            "low_stock_parts_count": low_stock_parts_count
        },
        "top_services": top_services_data,
        "six_months_revenue": six_months_revenue,
        "recent_activities": recent_activities
    }
