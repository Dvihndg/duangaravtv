# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import (
    Customer, Vehicle, Appointment, RepairOrder, RepairOrderStatus,
    Invoice, InvoiceStatus, Part, Service, RepairOrderItem
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
            RepairOrderStatus.DIAGNOSING,
            RepairOrderStatus.QUOTED,
            RepairOrderStatus.APPROVED,
            RepairOrderStatus.IN_PROGRESS
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
        "top_services": top_services_data
    }
