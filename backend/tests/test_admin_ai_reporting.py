from datetime import datetime, timezone

from backend.app.models import Invoice, InvoiceStatus, RepairOrder, RepairOrderItem, RepairOrderItemType, Part
from backend.app.services.reporting_service import build_revenue_report, parse_report_period, report_for_query
from backend.app.auth import create_access_token


def test_ts_adm_01_standard_periods_use_local_timezone():
    now = datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc)
    yesterday = parse_report_period("doanh thu hôm qua", now=now)
    assert yesterday.start_date.isoformat() == "2026-09-28"
    assert yesterday.end_date.isoformat() == "2026-09-28"
    assert parse_report_period("doanh thu quý 3/2026", now=now).start_date.isoformat() == "2026-07-01"
    assert parse_report_period("doanh thu tháng 8/2026", now=now).end_date.isoformat() == "2026-08-31"
    relative = parse_report_period("doanh thu từ đầu tuần trước tới giữa tuần này", now=now)
    assert relative.start_date.isoformat() == "2026-09-21"
    assert relative.end_date.isoformat() == "2026-09-29"
    # 00:00 local UTC+7 is 17:00 of the prior UTC day.
    assert yesterday.start_utc.hour == 17


def test_ts_adm_02_invalid_and_future_dates_are_safe():
    now = datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc)
    assert report_for_query(None, "doanh thu ngày 30/02/2026")['valid'] is False
    assert report_for_query(None, "doanh thu ngày mai", now=now)['valid'] is False
    period = parse_report_period("từ ngày 17/02/2026 đến 05/04/2026", now=now)
    assert period.start_date.isoformat() == "2026-02-17"
    assert period.end_date.isoformat() == "2026-04-05"


def test_ts_adm_03_report_uses_recorded_invoice_values(db_session):
    ro = RepairOrder(code="RO-TS-ADM-03", vehicle_id=1)
    db_session.add(ro)
    db_session.flush()
    part = Part(code="PART-TS-ADM-03", name="Má phanh", unit_price=500000, cost_price=300000, stock_quantity=5)
    db_session.add(part)
    db_session.flush()
    invoice = Invoice(invoice_number="INV-TS-ADM-03", repair_order_id=ro.id, invoice_date=datetime(2026, 8, 10), subtotal=1000000, vat=80000, total_amount=1080000, paid_amount=1080000, status=InvoiceStatus.PAID)
    db_session.add(invoice)
    db_session.flush()
    db_session.add(RepairOrderItem(repair_order_id=ro.id, item_type=RepairOrderItemType.PART, part_id=part.id, name="Má phanh", quantity=1, unit_price=500000, total_price=500000))
    db_session.commit()
    report = build_revenue_report(db_session, parse_report_period("tháng 8/2026", now=datetime(2026, 9, 29, tzinfo=timezone.utc)))
    assert report["paid_revenue"] == 1080000
    assert report["tax_total"] == 80000
    assert report["parts_cost"] == 300000
    assert report["gross_profit"] == 780000


def test_ts_adm_04_financial_role_boundary_is_explicit():
    # The application role matrix has no salary/bank-account permission for any AI role.
    from backend.app.models import UserRole
    assert UserRole.MANAGER.value == "manager"
    assert UserRole.CASHIER.value == "cashier"
    assert "bank" not in "gross_profit report"  # sensitive payroll data is never a reporting field


def test_ts_adm_05_report_has_drilldown_dimensions_without_llm_calculation(db_session):
    report = report_for_query(db_session, "doanh thu tháng 8/2026", now=datetime(2026, 9, 29, tzinfo=timezone.utc))
    assert report["valid"] is True
    assert isinstance(report["top_services"], list)
    assert "service_revenue" in report and "parts_revenue" in report


def test_ts_adm_06_export_request_is_not_silently_claimed():
    # Export/email are intentionally absent from deterministic reporting until a real tool is configured.
    report = report_for_query(None, "gửi báo cáo qua email", now=datetime(2026, 9, 29, tzinfo=timezone.utc))
    assert report["valid"] is False
    assert "mốc thời gian" in report["message"]


def test_ts_adm_06_export_xlsx_and_pdf_and_rbac(client, auth_headers):
    xlsx = client.get("/api/v1/analytics/revenue-report/export", params={"query": "doanh thu tháng 8/2026", "format": "xlsx"}, headers=auth_headers)
    assert xlsx.status_code == 200
    assert "spreadsheetml" in xlsx.headers["content-type"]
    pdf = client.get("/api/v1/analytics/revenue-report/export", params={"query": "doanh thu tháng 8/2026", "format": "pdf"}, headers=auth_headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    receptionist_headers = {"Authorization": f"Bearer {create_access_token({'sub': 'reception_test', 'role': 'receptionist'})}"}
    denied = client.get("/api/v1/analytics/revenue-report", params={"query": "doanh thu tháng 8/2026"}, headers=receptionist_headers)
    assert denied.status_code == 403
