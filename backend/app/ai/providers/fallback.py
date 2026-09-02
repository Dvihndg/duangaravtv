from typing import Dict, Any, List
from backend.app.ai.base import AIProvider

class FallbackProvider(AIProvider):
    """
    Smart Offline Fallback Engine:
    Vận hành 100% ngoại tuyến dựa trên quy tắc nghiệp vụ nội bộ khi không có Internet hoặc chưa cấu hình API Key.
    Bảo đảm hệ thống garage không bao giờ bị dừng hoạt động.
    """

    async def summarize_repair_history(
        self, 
        vehicle: Dict[str, Any], 
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        brand = vehicle.get("brand", "Xe")
        model = vehicle.get("model", "")
        plate = vehicle.get("license_plate", "")
        mileage = vehicle.get("current_mileage", 0)

        if not history:
            return {
                "vehicle_overview": f"Phương tiện {brand} {model} (Biển số {plate}), số km ghi nhận: {mileage:,} km. Đây là lần đầu tiên tiếp nhận tại xưởng.",
                "recent_repair_history": "Chưa có lịch sử sửa chữa trước đó tại Garage VTV.",
                "major_services": [],
                "parts_replaced": [],
                "repeated_observations": "Không phát hiện lịch sử hư hỏng lặp lại.",
                "important_notes": "Khuyến nghị thực hiện kiểm tra tổng quát 12 hạng mục tiêu chuẩn (Dầu máy, lọc dầu, nước làm mát, má phanh)."
            }

        total_visits = len(history)
        services_recorded = []
        parts_recorded = []
        for h in history:
            for s in h.get("services", []):
                services_recorded.append(s.get("name", ""))
            for p in h.get("parts", []):
                parts_recorded.append(p.get("name", ""))

        return {
            "vehicle_overview": f"Phương tiện {brand} {model} (Biển số {plate}), ODO hiện tại: {mileage:,} km. Đã thực hiện {total_visits} lần bảo dưỡng tại Garage.",
            "recent_repair_history": f"Lần gần nhất xe vào xưởng vào ngày {history[0].get('created_at', 'gần đây')}. Tình trạng ghi nhận: {history[0].get('customer_complaint', 'Bảo dưỡng')}.",
            "major_services": list(set(filter(None, services_recorded)))[:5],
            "parts_replaced": list(set(filter(None, parts_recorded)))[:5],
            "repeated_observations": "Không ghi nhận hỏng hóc lặp lại bất thường.",
            "important_notes": "Cần đối chiếu số km thực tế để khuyến cáo lịch thay thế định kỳ phụ tùng mòn theo thời gian."
        }

    async def explain_service(
        self, 
        repair_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        ro_code = repair_order.get("code", "RO")
        symptoms = repair_order.get("initial_symptoms") or "Bảo dưỡng định kỳ"
        diagnosis = repair_order.get("technical_diagnosis") or "Kiểm tra kỹ thuật hoàn tất"
        services = repair_order.get("services", [])
        parts = repair_order.get("parts", [])

        service_names = [s.get("name") for s in services if s.get("name")]
        part_names = [p.get("name") for p in parts if p.get("name")]

        expected = []
        if service_names:
            expected.append(f"Thực hiện dịch vụ: {', '.join(service_names)}")
        if part_names:
            expected.append(f"Thay thế linh kiện: {', '.join(part_names)}")

        return {
            "title": f"Giải Thích Phương Án Dịch Vụ - Phiếu #{ro_code}",
            "simple_explanation": f"Xe của quý khách được ghi nhận triệu chứng '{symptoms}'. Qua kiểm tra thực tế, đội ngũ kỹ thuật viên chẩn đoán: '{diagnosis}'. Để xe vận hành an toàn và mượt mà, xưởng đề xuất tiến hành các công việc theo danh mục chuẩn.",
            "expected_work": expected if expected else ["Kiểm tra và hiệu chỉnh tổng thể phương tiện"],
            "cost_information": "Toàn bộ chi phí công thợ và phụ tùng thay thế được niêm yết minh bạch, có hóa đơn VAT và phiếu bảo hành chính hãng kèm theo.",
            "important_note": "Các phụ tùng thay thế đều là linh kiện đạt tiêu chuẩn chất lượng. Quý khách vui lòng kiểm tra và duyệt báo giá trước khi bắt đầu thực hiện."
        }

    async def generate_draft_quotation(
        self, 
        services: List[Dict[str, Any]], 
        parts: List[Dict[str, Any]], 
        pricing: Dict[str, Any], 
        vat: float
    ) -> Dict[str, Any]:
        subtotal = pricing.get("subtotal", 0.0)
        total = pricing.get("total", 0.0)

        service_summary = ", ".join([s.get("name", "") for s in services if s.get("name")]) or "Dịch vụ bảo dưỡng"
        part_summary = ", ".join([p.get("name", "") for p in parts if p.get("name")]) or "Vật tư phụ tùng"

        return {
            "greeting": "Kính gửi Quý khách hàng! Garage VTV xin gửi tới Quý khách bảng dự toán chi phí dịch vụ kỹ thuật cho phương tiện.",
            "service_summary": service_summary,
            "parts_summary": part_summary,
            "pricing_note": f"Tổng giá trị dự kiến (đã bao gồm thuế VAT {vat*100:.0f}%): {total:,.0f} VNĐ. Chi phí chưa bao gồm các phát sinh ngoài dự kiến nếu chưa được sự đồng ý của Quý khách.",
            "warranty_terms": "Chính sách bảo hành: Bảo hành kỹ thuật công thợ 3 tháng, linh kiện phụ tùng theo tiêu chuẩn bảo hành chính hãng (6 - 12 tháng)."
        }
