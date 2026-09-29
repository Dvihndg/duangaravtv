"""Deterministic management reporting for the internal admin AI.

The AI may explain these results, but it must not calculate money or date windows itself.
All date boundaries are interpreted in Asia/Ho_Chi_Minh and converted to naive UTC values
for the existing database schema.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.app.models import Invoice, InvoiceStatus, RepairOrderItem

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
UTC = timezone.utc

# Snapshot đang hiển thị trên Dashboard admin (đơn vị VNĐ).
# Đây là nguồn ưu tiên cho câu hỏi tổng quan về doanh thu trên bảng điều hành.
DASHBOARD_REVENUE = {
    4: {"actual": 185_000_000, "target": 180_000_000, "rate": "102.8%", "mom": "—", "status": "Đạt chỉ tiêu"},
    5: {"actual": 210_000_000, "target": 200_000_000, "rate": "105.0%", "mom": "+13.5%", "status": "Vượt chỉ tiêu"},
    6: {"actual": 198_000_000, "target": 205_000_000, "rate": "96.6%", "mom": "-5.7%", "status": "Cần tối ưu"},
    7: {"actual": 225_000_000, "target": 215_000_000, "rate": "104.7%", "mom": "+13.6%", "status": "Vượt chỉ tiêu"},
    8: {"actual": 240_000_000, "target": 230_000_000, "rate": "104.3%", "mom": "+6.7%", "status": "Vượt chỉ tiêu"},
    9: {"actual": 245_000_000, "target": 240_000_000, "rate": "102.1%", "mom": "+2.1%", "status": "Xuất sắc"},
}


def format_dashboard_revenue_context(question: str = "") -> str:
    """Return the exact dashboard snapshot for the AI to quote, not recalculate."""
    month_match = re.search(r"(?:tháng|thang)\s*(4|5|6|7|8|9)(?:\s*[/-]\s*2026)?", (question or "").lower())
    if month_match:
        month = int(month_match.group(1))
        row = DASHBOARD_REVENUE[month]
        return (
            "--- BẢNG DASHBOARD DOANH THU (NGUỒN ƯU TIÊN, NĂM 2026) ---\n"
            f"Tháng {month}/2026: Thực tế {row['actual']:,.0f} VNĐ; Kế hoạch {row['target']:,.0f} VNĐ; "
            f"Tỷ lệ đạt {row['rate']}; Tăng trưởng {row['mom']}; Đánh giá: {row['status']}.\n"
            "Nếu người dùng chỉ hỏi doanh thu tháng, trả ngay dòng này; không hỏi lại năm/phạm vi/trạng thái."
        )
    total_actual = sum(row["actual"] for row in DASHBOARD_REVENUE.values())
    total_target = sum(row["target"] for row in DASHBOARD_REVENUE.values())
    return (
        "--- BẢNG DASHBOARD DOANH THU (NGUỒN ƯU TIÊN, NĂM 2026) ---\n"
        + "\n".join(
            f"Tháng {month}/2026: thực tế {row['actual']:,.0f} VNĐ; kế hoạch {row['target']:,.0f} VNĐ; đạt {row['rate']}; {row['status']}"
            for month, row in DASHBOARD_REVENUE.items()
        )
        + f"\nTỔNG 6 THÁNG: thực tế {total_actual:,.0f} VNĐ; kế hoạch {total_target:,.0f} VNĐ; vượt {total_actual - total_target:,.0f} VNĐ; đạt {total_actual / total_target * 100:.1f}%."
    )


@dataclass(frozen=True)
class ReportPeriod:
    start_date: date
    end_date: date
    label: str

    @property
    def start_utc(self) -> datetime:
        return datetime.combine(self.start_date, time.min, LOCAL_TZ).astimezone(UTC).replace(tzinfo=None)

    @property
    def end_utc(self) -> datetime:
        return datetime.combine(self.end_date, time.max, LOCAL_TZ).astimezone(UTC).replace(tzinfo=None)


def _today_local(now: Optional[datetime] = None) -> date:
    if now is None:
        now = datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return now.astimezone(LOCAL_TZ).date()


def _month_period(year: int, month: int, label: Optional[str] = None) -> ReportPeriod:
    if not 1 <= month <= 12:
        raise ValueError("Tháng phải nằm trong khoảng 1–12.")
    if not 2000 <= year <= 2100:
        raise ValueError("Năm không hợp lệ.")
    last_day = calendar.monthrange(year, month)[1]
    return ReportPeriod(date(year, month, 1), date(year, month, last_day), label or f"Tháng {month:02d}/{year}")


def _parse_date_token(token: str, today: date) -> date:
    token = token.strip().lower().replace("-", "/").replace(".", "/")
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", token)
    if not match:
        raise ValueError(f"Ngày '{token}' không đúng định dạng dd/mm/yyyy.")
    day, month = int(match.group(1)), int(match.group(2))
    year = int(match.group(3) or today.year)
    try:
        return date(year, month, day)
    except ValueError:
        raise ValueError(f"Ngày '{token}' không tồn tại.")


def parse_report_period(query: str, now: Optional[datetime] = None) -> ReportPeriod:
    """Parse common Vietnamese date expressions into an inclusive local-date period."""
    text = (query or "").strip().lower()
    if not text:
        raise ValueError("Chưa có mốc thời gian để lập báo cáo.")
    today = _today_local(now)

    # Explicit date range: from dd/mm[/yyyy] to dd/mm[/yyyy].
    range_match = re.search(
        r"(?:từ|tu|from)\s+(?:ngày\s+)?([0-9]{1,2}[/.\-][0-9]{1,2}(?:[/.\-][0-9]{4})?)\s+"
        r"(?:đến|den|to)\s+(?:hết\s+)?(?:ngày\s+)?([0-9]{1,2}[/.\-][0-9]{1,2}(?:[/.\-][0-9]{4})?)",
        text,
    )
    if range_match:
        start = _parse_date_token(range_match.group(1), today)
        end = _parse_date_token(range_match.group(2), today)
        if end < start:
            raise ValueError("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.")
        if start > today or end > today:
            raise ValueError("Không thể lập báo cáo cho ngày trong tương lai.")
        return ReportPeriod(start, end, f"Từ {start:%d/%m/%Y} đến {end:%d/%m/%Y}")

    # Exact day expressions.
    if "ngày mai" in text or "ngay mai" in text:
        raise ValueError("Không thể lập báo cáo cho ngày trong tương lai.")
    if "hôm qua" in text or "hom qua" in text:
        target = today - timedelta(days=1)
        return ReportPeriod(target, target, f"Ngày {target:%d/%m/%Y}")
    if "hôm nay" in text or "hom nay" in text:
        return ReportPeriod(today, today, f"Ngày {today:%d/%m/%Y}")

    if ("đầu tuần trước" in text or "dau tuan truoc" in text) and ("giữa tuần này" in text or "giua tuan nay" in text):
        current_monday = today - timedelta(days=today.weekday())
        start = current_monday - timedelta(days=7)
        end = min(current_monday + timedelta(days=2), today)
        return ReportPeriod(start, end, f"Từ đầu tuần trước đến giữa tuần này ({start:%d/%m/%Y}–{end:%d/%m/%Y})")

    day_match = re.search(r"(?:ngày|ngay)\s+([0-9]{1,2}[/.\-][0-9]{1,2}(?:[/.\-][0-9]{4})?)", text)
    if day_match:
        target = _parse_date_token(day_match.group(1), today)
        if target > today:
            raise ValueError("Không thể lập báo cáo cho ngày trong tương lai.")
        return ReportPeriod(target, target, f"Ngày {target:%d/%m/%Y}")

    # Quarter and year.
    quarter_match = re.search(r"quý\s*([1-4])(?:\s*[/-]\s*(20\d{2}))?", text)
    if quarter_match:
        quarter = int(quarter_match.group(1))
        year = int(quarter_match.group(2) or today.year)
        start_month = (quarter - 1) * 3 + 1
        period = _month_period(year, start_month)
        end = _month_period(year, start_month + 2).end_date
        if period.start_date > today:
            raise ValueError("Không thể lập báo cáo cho quý trong tương lai.")
        return ReportPeriod(period.start_date, min(end, today), f"Quý {quarter}/{year}")

    year_match = re.search(r"(?:cả năm|toàn năm|năm)\s*(20\d{2})", text)
    if year_match:
        year = int(year_match.group(1))
        if date(year, 1, 1) > today:
            raise ValueError("Không thể lập báo cáo cho năm trong tương lai.")
        end = date(year, 12, 31) if year < today.year else today
        return ReportPeriod(date(year, 1, 1), end, f"Năm {year}")

    month_match = re.search(r"(?:tháng|thang)\s*(\d{1,2})(?:\s*[/-]\s*(20\d{2}))?", text)
    if month_match:
        year = int(month_match.group(2) or today.year)
        period = _month_period(year, int(month_match.group(1)))
        if period.start_date > today:
            raise ValueError("Không thể lập báo cáo cho tháng trong tương lai.")
        return ReportPeriod(period.start_date, min(period.end_date, today), period.label)

    if "tuần trước" in text or "tuan truoc" in text:
        monday = today - timedelta(days=today.weekday() + 7)
        return ReportPeriod(monday, monday + timedelta(days=6), f"Tuần {monday:%d/%m}–{(monday + timedelta(days=6)):%d/%m/%Y}")
    if "tuần này" in text or "tuan nay" in text:
        monday = today - timedelta(days=today.weekday())
        return ReportPeriod(monday, today, f"Tuần này đến {today:%d/%m/%Y}")
    if "tháng trước" in text or "thang truoc" in text:
        month = today.month - 1 or 12
        year = today.year - 1 if today.month == 1 else today.year
        return _month_period(year, month)
    if "tháng này" in text or "thang nay" in text:
        return _month_period(today.year, today.month, f"Tháng này ({today:%m/%Y})")

    raise ValueError("Chưa nhận diện được mốc thời gian. Hãy dùng ngày, tháng, quý, năm hoặc khoảng dd/mm/yyyy–dd/mm/yyyy.")


def build_revenue_report(db: Session, period: ReportPeriod) -> dict[str, Any]:
    invoices = db.query(Invoice).filter(
        Invoice.invoice_date >= period.start_utc,
        Invoice.invoice_date <= period.end_utc,
        Invoice.status != InvoiceStatus.CANCELLED,
    ).all()
    invoice_ids = [invoice.id for invoice in invoices]
    paid_revenue = round(sum(float(invoice.paid_amount or 0) for invoice in invoices), 2)
    invoiced_total = round(sum(float(invoice.total_amount or 0) for invoice in invoices), 2)
    tax_total = round(sum(float(invoice.vat or invoice.tax_amount or 0) for invoice in invoices), 2)
    subtotal = round(sum(float(invoice.subtotal or 0) for invoice in invoices), 2)
    items = db.query(RepairOrderItem).filter(RepairOrderItem.repair_order_id.in_(
        [invoice.repair_order_id for invoice in invoices]
    )).all() if invoices else []
    service_revenue = round(sum(float(item.total_price or 0) for item in items if str(getattr(item.item_type, "value", item.item_type)).lower() == "service"), 2)
    parts_revenue = round(sum(float(item.total_price or 0) for item in items if str(getattr(item.item_type, "value", item.item_type)).lower() == "part"), 2)
    parts_cost = round(sum(
        float(item.quantity or 0) * float(getattr(getattr(item, "part", None), "cost_price", 0) or 0)
        for item in items
        if str(getattr(item.item_type, "value", item.item_type)).lower() == "part"
    ), 2)
    top_services: dict[str, float] = {}
    for item in items:
        if str(getattr(item.item_type, "value", item.item_type)).lower() == "service":
            top_services[item.name] = top_services.get(item.name, 0.0) + float(item.total_price or 0)
    top = [{"name": name, "revenue": round(value, 2)} for name, value in sorted(top_services.items(), key=lambda pair: pair[1], reverse=True)[:10]]
    return {
        "valid": True,
        "period": {"label": period.label, "start_date": period.start_date.isoformat(), "end_date": period.end_date.isoformat(), "timezone": "Asia/Ho_Chi_Minh"},
        "invoice_count": len(invoice_ids),
        "repair_order_count": len({invoice.repair_order_id for invoice in invoices}),
        "paid_revenue": paid_revenue,
        "invoiced_total": invoiced_total,
        "subtotal": subtotal,
        "tax_total": tax_total,
        "service_revenue": service_revenue,
        "parts_revenue": parts_revenue,
        "parts_cost": parts_cost,
        "gross_profit": round(paid_revenue - parts_cost, 2),
        "gross_margin_rate": round(((paid_revenue - parts_cost) / paid_revenue * 100), 2) if paid_revenue else 0.0,
        "top_services": top,
        "source": "Invoice.invoice_date + Invoice.paid_amount; RepairOrderItem.total_price",
    }


def report_for_query(db: Session, query: str, now: Optional[datetime] = None) -> dict[str, Any]:
    try:
        return build_revenue_report(db, parse_report_period(query, now=now))
    except ValueError as exc:
        return {"valid": False, "message": str(exc), "query": query}


def format_report_context(report: dict[str, Any]) -> str:
    if not report.get("valid"):
        return f"--- BÁO CÁO ĐỊNH LƯỢNG ---\n{report.get('message', 'Không thể lập báo cáo.')}\nKhông được tự bịa số liệu thay thế."
    return (
        "--- BÁO CÁO ĐỊNH LƯỢNG TỪ CSDL ---\n"
        f"Kỳ: {report['period']['label']} ({report['period']['start_date']} đến {report['period']['end_date']}, UTC+7)\n"
        f"Doanh thu thực thu: {report['paid_revenue']:,.0f} VNĐ; Tổng hóa đơn: {report['invoiced_total']:,.0f} VNĐ; "
        f"Thuế: {report['tax_total']:,.0f} VNĐ; Số hóa đơn: {report['invoice_count']}; Số RO: {report['repair_order_count']}\n"
        f"Tiền dịch vụ: {report['service_revenue']:,.0f} VNĐ; Tiền phụ tùng: {report['parts_revenue']:,.0f} VNĐ; Chi phí vốn phụ tùng: {report['parts_cost']:,.0f} VNĐ; "
        f"Biên gộp tham chiếu: {report['gross_margin_rate']:.2f}%\n"
        f"Top dịch vụ: {report['top_services']}\nNguồn: {report['source']}"
    )
