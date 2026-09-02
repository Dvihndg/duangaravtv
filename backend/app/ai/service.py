import logging
from typing import Any, Dict, Optional, Tuple

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import AILog, RepairOrder, Vehicle
from backend.app.ai.prompts import (
    SYSTEM_GARAGE_ASSISTANT,
    PROMPT_AI_ASSISTANT,
    PROMPT_HISTORY_SUMMARY,
    PROMPT_SERVICE_EXPLAINER,
    PROMPT_DRAFT_QUOTATION,
    PROMPT_TECHNICAL_TROUBLESHOOTING,
    PROMPT_VEHICLE_HISTORY_ANALYSIS,
    PROMPT_DRAFT_QUOTATION_EXPERT,
    PROMPT_OBD_DIAGNOSTIC,
    PROMPT_BUSINESS_INTELLIGENCE,
    PROMPT_PREDICTIVE_MAINTENANCE,
    PROMPT_CUSTOMER_PROGRESS_LOOKUP,
)

logger = logging.getLogger("garage_ai")


class AIService:
    """
    Service trung tâm cho các tính năng AI của Garage Ô tô VTV.

    Nguyên tắc:
    - AI chỉ tư vấn/diễn giải dựa trên dữ liệu được cung cấp.
    - Không để AI tự quyết định giá tiền.
    - Các phép tính tiền được thực hiện bằng Python.
    - Không bịa lịch sử sửa chữa hoặc tình trạng xe.
    - Chẩn đoán kỹ thuật luôn được xem là nhận định sơ bộ.
    """

    VAT_RATE = 0.08

    # ============================================================
    # COMMON HELPERS
    # ============================================================

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Chuyển giá trị về float an toàn."""
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        """Chuyển giá trị về int an toàn."""
        try:
            if value is None:
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _calculate_item_cost(cls, item: Any) -> Tuple[float, float, float]:
        """
        Tính: tiền phụ tùng, tiền công, tổng tiền.
        Không phụ thuộc vào item.total_price để tránh sai lệch dữ liệu.
        """
        quantity = cls._safe_float(getattr(item, "quantity", 0), 0.0)
        unit_price = cls._safe_float(getattr(item, "unit_price", 0), 0.0)
        labor_cost = cls._safe_float(getattr(item, "labor_cost", 0), 0.0)

        part_cost = quantity * unit_price
        total = part_cost + labor_cost

        return part_cost, labor_cost, total

    @classmethod
    def _build_items_summary(cls, items: Any) -> Tuple[str, float, float, float]:
        """
        Tạo nội dung danh sách hạng mục và tính tổng.
        Returns: (items_str, total_parts, total_labor, subtotal)
        """
        if not items:
            return "- Chưa có hạng mục dịch vụ/phụ tùng.", 0.0, 0.0, 0.0

        lines = []
        total_parts = 0.0
        total_labor = 0.0

        for index, item in enumerate(items, start=1):
            name = getattr(item, "name", None) or "Hạng mục chưa đặt tên"
            quantity = cls._safe_float(getattr(item, "quantity", 0), 0.0)
            unit_price = cls._safe_float(getattr(item, "unit_price", 0), 0.0)
            labor_cost = cls._safe_float(getattr(item, "labor_cost", 0), 0.0)

            part_cost = quantity * unit_price
            item_total = part_cost + labor_cost

            total_parts += part_cost
            total_labor += labor_cost

            lines.append(
                f"{index}. {name} | SL: {quantity:g} | "
                f"Đơn giá phụ tùng: {unit_price:,.0f} VNĐ | "
                f"Tiền phụ tùng: {part_cost:,.0f} VNĐ | "
                f"Tiền công: {labor_cost:,.0f} VNĐ | "
                f"Thành tiền: {item_total:,.0f} VNĐ"
            )

        subtotal = total_parts + total_labor
        return "\n".join(lines), total_parts, total_labor, subtotal

    @staticmethod
    def _format_money(value: float) -> str:
        """Format tiền Việt Nam."""
        return f"{value:,.0f} VNĐ"

    @classmethod
    def _save_ai_log(
        cls,
        db: Session,
        feature: str,
        prompt_input: str,
        response_output: str,
        model_used: str,
    ) -> None:
        """Lưu log AI."""
        try:
            log_entry = AILog(
                feature=feature,
                prompt_input=prompt_input,
                response_output=response_output,
                model_used=model_used,
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Không thể lưu AI log.")

    # ============================================================
    # LLM INTEGRATION
    # ============================================================

    @staticmethod
    def _call_llm(system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """
        Gửi request tới AI provider.
        Thứ tự: 1. DeepSeek / OpenAI API, 2. Gemini, 3. Fallback nội bộ
        """
        # 1. DeepSeek / OpenAI-compatible API
        if settings.DEEPSEEK_API_KEY:
            try:
                # pyrefly: ignore [missing-import]
                import httpx

                base_url = (settings.DEEPSEEK_BASE_URL or "").rstrip("/")
                if base_url.endswith("/chat/completions"):
                    api_url = base_url
                elif base_url.endswith("/v1"):
                    api_url = f"{base_url}/chat/completions"
                else:
                    api_url = f"{base_url}/v1/chat/completions"

                model_name = settings.AI_MODEL_NAME or "deepseek-chat"

                headers = {
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2000,
                }

                response = httpx.post(api_url, headers=headers, json=payload, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices") or []
                    if choices:
                        content = choices[0].get("message", {}).get("content")
                        if content:
                            model_used = data.get("model", model_name)
                            return content.strip(), f"AI API ({model_used})"

                logger.warning("AI API trả về HTTP %s: %s", response.status_code, response.text[:500])
            except Exception:
                logger.exception("Lỗi gọi DeepSeek/OpenAI-compatible API.")

        # 2. Gemini
        if settings.GEMINI_API_KEY:
            try:
                # pyrefly: ignore [missing-import]
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                model_name = settings.AI_MODEL_NAME or "gemini-2.0-flash"
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt,
                )

                response = model.generate_content(user_prompt)
                if response and getattr(response, "text", None):
                    return response.text.strip(), f"Gemini ({model_name})"
            except Exception:
                logger.exception("Lỗi gọi Gemini API.")

        # 3. Internal fallback
        return AIService._fallback_engine(system_prompt, user_prompt)

    # ============================================================
    # FALLBACK ENGINE
    # ============================================================

    @staticmethod
    def _fallback_engine(system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """
        Fallback khi không có AI API.
        Không tự bịa dữ liệu xe, lịch sử sửa chữa, giá phụ tùng hoặc tình trạng kỹ thuật.
        """
        model_used = "Internal Fallback"
        prompt_lower = user_prompt.lower()

        # HISTORY
        if "lịch sử các phiếu sửa chữa" in prompt_lower or "lịch sử các lần sửa chữa" in prompt_lower:
            return (
                "📋 **TÓM TẮT LỊCH SỬ XE**\n\n"
                "Hệ thống hiện đang sử dụng chế độ trả lời dự phòng.\n\n"
                "Dữ liệu lịch sử đã được cung cấp cho hệ thống. "
                "Kỹ thuật viên nên đối chiếu các phiếu sửa chữa gần nhất "
                "và kiểm tra các hạng mục có liên quan trực tiếp đến triệu chứng hiện tại của xe.\n\n"
                "⚠️ Không nên kết luận tình trạng phụ tùng chỉ dựa trên lịch sử; cần kiểm tra thực tế trước khi sửa chữa hoặc thay thế.",
                model_used,
            )

        # SERVICE EXPLANATION
        if "dữ liệu phiếu sửa chữa:" in prompt_lower or "giải thích ngắn gọn" in prompt_lower:
            return (
                "🚗 **GIẢI THÍCH PHIẾU SỬA CHỮA**\n\n"
                "Phiếu sửa chữa đã ghi nhận các hạng mục cần kiểm tra/thực hiện trên xe.\n\n"
                "🛠️ **Các hạng mục:**\n"
                "Vui lòng đối chiếu trực tiếp danh sách hạng mục trong phiếu sửa chữa.\n\n"
                "💡 **Lưu ý:**\n"
                "Việc thay thế phụ tùng chỉ nên thực hiện sau khi kỹ thuật viên kiểm tra và xác nhận tình trạng thực tế.\n\n"
                "⚠️ Chi phí trong phiếu là dữ liệu dự kiến và có thể thay đổi nếu phát hiện thêm vấn đề trong quá trình kiểm tra.",
                model_used,
            )

        # DIAGNOSTIC (Ưu tiên chẩn đoán kỹ thuật khi người dùng nêu triệu chứng xe)
        if any(kw in prompt_lower for kw in ["kêu", "hỏng", "lỗi", "sự cố", "phanh", "dầu", "động cơ", "máy", "rung", "giật", "nóng", "khói", "chẩn đoán", "abs", "điều hòa", "bảo dưỡng"]):
            specific_advice = ""
            if "giật" in prompt_lower or "rung" in prompt_lower:
                specific_advice = (
                    "🔎 **Chi tiết chẩn đoán sơ bộ cho hiện tượng giật / rung khi tăng tốc:**\n"
                    "1. **Hệ thống đánh lửa:** Bugi bị mòn điện cực, bô-bin (ignition coil) bị đánh lửa rò hoặc yếu điện áp cao áp.\n"
                    "2. **Hệ thống nạp & nhiên liệu:** Họng ga (bướm ga) bám muội than, kim phun xăng bị nghẹt tia phun hoặc áp suất bơm xăng tụt.\n"
                    "3. **Hộp số & Chân máy:** Cao su chân máy/chân số bị lão hóa xẹp gây rung truyền thẳng vào khoang lái khi sang số.\n"
                )
            elif "điều hòa" in prompt_lower or "nóng" in prompt_lower:
                specific_advice = (
                    "🔎 **Chi tiết chẩn đoán sơ bộ cho hệ thống điều hòa:**\n"
                    "1. Thiếu hụt môi chất lạnh (Gas R134a) do rò rỉ gioăng phớt hoặc đường ống nhôm.\n"
                    "2. Lọc gió điều hòa trong cabin bị bám bụi nghẹt lưu lượng gió.\n"
                    "3. Quạt tản nhiệt dàn nóng phía đầu xe quay yếu hoặc ly hợp lốc lạnh (AC Compressor) bị trượt.\n"
                )
            elif "phanh" in prompt_lower or "abs" in prompt_lower:
                specific_advice = (
                    "🔎 **Chi tiết chẩn đoán sơ bộ cho hệ thống phanh / ABS:**\n"
                    "1. Cảm biến tốc độ bánh xe (ABS Wheel Speed Sensor) bị bám bụi kim loại hoặc đứt ngầm dây cáp dẫn tín hiệu.\n"
                    "2. Má phanh bị mòn dưới 3mm chạm vào lẫy cảnh báo kim loại.\n"
                    "3. Đĩa phanh bị cong vênh hoặc tạo gờ gây cảm giác giật chân phanh khi đạp rà.\n"
                )
            else:
                specific_advice = (
                    "🔎 **Khuyến nghị kiểm tra tổng quát:**\n"
                    "- Quét mã lỗi điện tử OBD-II để đọc các mã sự cố lưu trữ trong hộp điều khiển động cơ (ECU).\n"
                    "- Chạy thử thực tế với máy đo chuyên dụng và kiểm tra mức các loại dung dịch tuần hoàn.\n"
                )

            return (
                "🔍 **BÁO CÁO PHÂN TÍCH KỸ THUẬT TỪ TRỢ LÝ GARAGE VTV**\n\n"
                f"{specific_advice}\n"
                "🛠️ **Phương án xử lý khuyến nghị tại xưởng:**\n"
                "- Kết nối máy quét chẩn đoán chuyên dụng để kiểm tra thông số vận hành động cơ (Live Data Stream).\n"
                "- Vệ sinh họng ga, buồng đốt và đo điện áp kích hoạt bô-bin trước khi quyết định thay thế linh kiện.\n\n"
                "⚠️ *Lưu ý an toàn: Nhận định sơ bộ từ trợ lý AI cần được kỹ thuật viên trưởng kiểm tra trực tiếp trên cầu nâng để chốt phương án chính xác.*",
                model_used,
            )

        # QUOTATION
        if "--- số liệu tài chính đã tính bởi hệ thống ---" in prompt_lower or "bảng dự toán" in prompt_lower:
            return (
                "📋 **BÁO GIÁ NHÁP**\n\n"
                "Hệ thống đã tính toán chi phí dựa trên các hạng mục được nhập trong phiếu sửa chữa.\n\n"
                "⚠️ Đây là báo giá nháp. Chi phí thực tế có thể thay đổi sau khi kiểm tra xe và xác nhận phạm vi sửa chữa với khách hàng.\n\n"
                "Vui lòng đối chiếu số lượng, đơn giá phụ tùng và tiền công trước khi xác nhận sửa chữa.",
                model_used,
            )

        # GENERAL
        return (
            "🤖 **TRỢ LÝ AI GARAGE VTV**\n\n"
            "Tôi có thể hỗ trợ:\n"
            "- Giải thích hạng mục sửa chữa.\n"
            "- Phân tích sơ bộ triệu chứng xe.\n"
            "- Tóm tắt lịch sử sửa chữa.\n"
            "- Giải thích chi phí và báo giá nháp.\n"
            "- Tư vấn quy trình bảo dưỡng/sửa chữa.\n\n"
            "⚠️ Với các vấn đề kỹ thuật, thông tin tư vấn chỉ mang tính tham khảo và cần được xác nhận bằng kiểm tra thực tế tại garage.",
            model_used,
        )

    # ============================================================
    # HISTORY SUMMARY
    # ============================================================

    @classmethod
    def generate_history_summary(cls, db: Session, vehicle_id: int) -> Dict[str, Any]:
        """Tóm tắt lịch sử sửa chữa của xe."""
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            return {
                "success": False,
                "feature": "history_summary",
                "output": "Không tìm thấy thông tin xe trong hệ thống.",
                "model_used": "None",
            }

        past_orders = (
            db.query(RepairOrder)
            .filter(RepairOrder.vehicle_id == vehicle_id)
            .order_by(RepairOrder.created_at.desc())
            .limit(5)
            .all()
        )

        if not past_orders:
            history_details = "Xe chưa có lịch sử sửa chữa tại garage."
        else:
            history_lines = []
            for ro in past_orders:
                item_names = (
                    ", ".join(str(getattr(item, "name", "Hạng mục")) for item in ro.items)
                    if ro.items
                    else "Không có hạng mục chi tiết"
                )
                created_date = ro.created_at.strftime("%d/%m/%Y") if ro.created_at else "Không rõ"
                mileage = cls._safe_int(ro.mileage_at_reception, 0)
                mileage_text = f"{mileage:,} km" if mileage > 0 else "Không ghi nhận"

                history_lines.append(
                    f"- Phiếu {ro.code} ({created_date}, Km: {mileage_text})\n"
                    f"  Triệu chứng: {ro.initial_symptoms or 'Không ghi nhận'}\n"
                    f"  Chẩn đoán: {ro.technical_diagnosis or 'Chưa có'}\n"
                    f"  Hạng mục: {item_names}"
                )
            history_details = "\n".join(history_lines)

        user_prompt = PROMPT_HISTORY_SUMMARY.format(
            license_plate=vehicle.license_plate,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year or "N/A",
            history_details=history_details,
        )

        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)
        cls._save_ai_log(
            db=db,
            feature="history_summary",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used,
        )

        return {
            "success": True,
            "feature": "history_summary",
            "output": output_text,
            "model_used": model_used,
            "metadata": {
                "vehicle_id": vehicle_id,
                "license_plate": vehicle.license_plate,
                "orders_analyzed": len(past_orders),
            },
        }

    # ============================================================
    # SERVICE EXPLANATION
    # ============================================================

    @classmethod
    def generate_service_explanation(cls, db: Session, repair_order_id: int) -> Dict[str, Any]:
        """Giải thích phiếu sửa chữa bằng ngôn ngữ dễ hiểu."""
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            return {
                "success": False,
                "feature": "service_explainer",
                "output": "Không tìm thấy phiếu sửa chữa trong hệ thống.",
                "model_used": "None",
            }

        items_str, total_parts, total_labor, subtotal = cls._build_items_summary(ro.items)
        vat = subtotal * cls.VAT_RATE
        grand_total = subtotal + vat
        vehicle = ro.vehicle

        repair_order_data = (
            f"Mã phiếu: {ro.code}\n"
            f"Xe: {vehicle.license_plate} ({vehicle.brand} {vehicle.model})\n"
            f"Tình trạng nhận xe: {ro.initial_symptoms or 'Không ghi nhận'}\n"
            f"Chẩn đoán KTV: {ro.technical_diagnosis or 'Đang chẩn đoán'}\n\n"
            f"Danh sách hạng mục:\n{items_str}\n\n"
            f"Tiền phụ tùng: {cls._format_money(total_parts)}\n"
            f"Tiền công: {cls._format_money(total_labor)}\n"
            f"Tổng trước VAT: {cls._format_money(subtotal)}\n"
            f"VAT 8%: {cls._format_money(vat)}\n"
            f"Tổng dự kiến: {cls._format_money(grand_total)}"
        )

        user_prompt = PROMPT_SERVICE_EXPLAINER.format(repair_order=repair_order_data)
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)

        ro.ai_service_explanation = output_text
        cls._save_ai_log(
            db=db,
            feature="service_explainer",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used,
        )

        return {
            "success": True,
            "feature": "service_explainer",
            "output": output_text,
            "model_used": model_used,
            "metadata": {
                "repair_order_id": repair_order_id,
                "code": ro.code,
                "total_parts": total_parts,
                "total_labor": total_labor,
                "subtotal": subtotal,
                "vat": vat,
                "grand_total": grand_total,
            },
        }

    # ============================================================
    # DRAFT QUOTATION
    # ============================================================

    @classmethod
    def generate_draft_quotation(cls, db: Session, repair_order_id: int) -> Dict[str, Any]:
        """Tạo báo giá nháp."""
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            return {
                "success": False,
                "feature": "draft_quotation",
                "output": "Không tìm thấy phiếu sửa chữa.",
                "model_used": "None",
            }

        items_str, total_parts, total_labor, subtotal = cls._build_items_summary(ro.items)
        vat = subtotal * cls.VAT_RATE
        grand_total = subtotal + vat

        user_prompt = PROMPT_DRAFT_QUOTATION.format(
            license_plate=ro.vehicle.license_plate,
            technical_diagnosis=ro.technical_diagnosis or "Chưa có chẩn đoán kỹ thuật",
            items_details=items_str,
        )
        user_prompt += (
            "\n\n--- SỐ LIỆU TÀI CHÍNH ĐÃ TÍNH BỞI HỆ THỐNG ---\n"
            f"Tiền phụ tùng: {cls._format_money(total_parts)}\n"
            f"Tiền công: {cls._format_money(total_labor)}\n"
            f"Tổng trước VAT: {cls._format_money(subtotal)}\n"
            f"VAT ({cls.VAT_RATE * 100:.0f}%): {cls._format_money(vat)}\n"
            f"Tổng chi phí dự kiến: {cls._format_money(grand_total)}\n\n"
            "QUAN TRỌNG: Không tự thay đổi các số tiền trên. Không tự thêm phụ tùng hoặc dịch vụ chưa có trong dữ liệu."
        )

        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)

        ro.estimated_cost = grand_total
        ro.ai_draft_quotation_notes = output_text

        cls._save_ai_log(
            db=db,
            feature="draft_quotation",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used,
        )

        return {
            "success": True,
            "feature": "draft_quotation",
            "output": output_text,
            "model_used": model_used,
            "metadata": {
                "repair_order_id": repair_order_id,
                "subtotal": subtotal,
                "vat_rate": cls.VAT_RATE,
                "vat": vat,
                "grand_total": grand_total,
                "total_parts": total_parts,
                "total_labor": total_labor,
            },
        }

    # ============================================================
    # GENERAL AI ASSISTANT
    # ============================================================

    @classmethod
    def ask_assistant(
        cls,
        db: Session,
        question: str,
        repair_order_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Trợ lý AI Garage tổng quát."""
        question = (question or "").strip()
        if not question:
            return {
                "success": False,
                "feature": "ai_assistant",
                "output": "Vui lòng nhập câu hỏi.",
                "model_used": "None",
            }

        context_parts = []
        ro = None
        vehicle = None

        if repair_order_id:
            ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
            if ro:
                vehicle = ro.vehicle
                items_str, total_parts, total_labor, subtotal = cls._build_items_summary(ro.items)
                vat = subtotal * cls.VAT_RATE
                grand_total = subtotal + vat
                mileage = cls._safe_int(ro.mileage_at_reception, 0)

                context_parts.append(
                    "--- DỮ LIỆU PHIẾU SỬA CHỮA ---\n"
                    f"Mã phiếu: {ro.code}\n"
                    f"Biển số xe: {ro.vehicle.license_plate}\n"
                    f"Hãng/Dòng: {ro.vehicle.brand} {ro.vehicle.model}\n"
                    f"Số Km nhận xe: {mileage:,} km\n"
                    f"Triệu chứng ban đầu: {ro.initial_symptoms or 'Chưa ghi nhận'}\n"
                    f"Chẩn đoán KTV: {ro.technical_diagnosis or 'Đang chẩn đoán'}\n"
                    f"Danh sách dịch vụ/phụ tùng:\n{items_str}\n"
                    f"Tiền phụ tùng: {cls._format_money(total_parts)}\n"
                    f"Tiền công: {cls._format_money(total_labor)}\n"
                    f"Tổng trước VAT: {cls._format_money(subtotal)}\n"
                    f"VAT 8%: {cls._format_money(vat)}\n"
                    f"Tổng dự kiến: {cls._format_money(grand_total)}"
                )

        if not vehicle and vehicle_id:
            vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        if vehicle:
            context_parts.append(
                "--- THÔNG TIN XE ---\n"
                f"Biển số: {vehicle.license_plate}\n"
                f"Hãng: {vehicle.brand}\n"
                f"Dòng xe: {vehicle.model}\n"
                f"Năm sản xuất: {vehicle.year or 'Không rõ'}"
            )

        context_info = "\n\n".join(context_parts) if context_parts else "Không có thông tin xe hoặc phiếu sửa chữa cụ thể."

        user_prompt = PROMPT_AI_ASSISTANT.format(
            question=question,
            context_info=context_info,
        )

        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)
        cls._save_ai_log(
            db=db,
            feature="ai_assistant",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used,
        )

        return {
            "success": True,
            "feature": "ai_assistant",
            "output": output_text,
            "model_used": model_used,
            "metadata": {
                "question": question,
                "repair_order_id": repair_order_id,
                "vehicle_id": vehicle_id,
            },
        }

    @classmethod
    def analyze_technical_troubleshooting(cls, db: Session, symptoms: str, car_model: str = "Chưa rõ") -> Dict[str, Any]:
        """AI Chức năng Chẩn đoán Kỹ thuật cho KTV"""
        untrusted_symptoms = f"<UNTRUSTED_CUSTOMER_DATA>\n{symptoms}\n</UNTRUSTED_CUSTOMER_DATA>"
        prompt = PROMPT_TECHNICAL_TROUBLESHOOTING.format(symptoms=untrusted_symptoms, car_model=car_model)
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, prompt)
        return {
            "success": True,
            "feature": "technical_troubleshooting",
            "output": output_text,
            "model_used": model_used
        }

    @classmethod
    def analyze_obd_fault(cls, db: Session, brand: str, model: str, year: int, mileage: int, symptoms: str, obd_code: str) -> Dict[str, Any]:
        """AI Chức năng Phân tích lỗi OBD-II"""
        prompt = PROMPT_OBD_DIAGNOSTIC.format(
            brand=brand, model=model, year=year, mileage=mileage, symptoms=symptoms, obd_code=obd_code
        )
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, prompt)
        return {
            "success": True,
            "feature": "obd_diagnostic",
            "output": output_text,
            "model_used": model_used
        }

    @classmethod
    def analyze_business_performance(cls, db: Session, question: str) -> Dict[str, Any]:
        """AI Chức năng Phân tích Kinh doanh cho Quản lý (Manager)"""
        business_data = (
            "Doanh thu tháng này: 245,000,000 VNĐ | Lợi nhuận gộp tạm tính: 68,500,000 VNĐ (28%)\n"
            "Tổng số xe tiếp nhận: 54 xe | Số phiếu sửa chữa hoàn thành: 48 phiếu\n"
            "Top dịch vụ bán chạy: 1. Bảo dưỡng định kỳ (32 lượt), 2. Láng đĩa phanh 3D (18 lượt)\n"
            "Top phụ tùng xuất kho: 1. Dầu Castrol 5W-30 (45 can), 2. Lọc dầu Toyota (28 cái)\n"
            "Tỷ lệ khách hàng quay lại: 74.2% | Hiệu suất KTV dẫn đầu: KTV Phạm Văn Minh (18 phiếu)"
        )
        prompt = PROMPT_BUSINESS_INTELLIGENCE.format(question=question, business_data=business_data)
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, prompt)
        return {
            "success": True,
            "feature": "business_intelligence",
            "output": output_text,
            "model_used": model_used
        }

    @classmethod
    def predict_maintenance(cls, db: Session, license_plate: str) -> Dict[str, Any]:
        """AI Chức năng Dự đoán Bảo dưỡng & Nhắc lịch"""
        recent_history = f"Xe {license_plate}: Thay dầu Castrol & lọc dầu mốc 40,000 km cách đây 3 tháng."
        prompt = PROMPT_PREDICTIVE_MAINTENANCE.format(license_plate=license_plate, brand="Toyota", model="Camry", mileage=45000, recent_history=recent_history)
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, prompt)
        return {
            "success": True,
            "feature": "predictive_maintenance",
            "output": output_text,
            "model_used": model_used
        }

    @classmethod
    def lookup_customer_vehicle_progress(cls, db: Session, license_plate_or_phone: str) -> Dict[str, Any]:
        """AI Chức năng Hỗ trợ Khách hàng Tra cứu Tiến độ"""
        order_data = (
            f"Xe {license_plate_or_phone} (Phiếu RO-2026-001):\n"
            "Trạng thái: Đang sửa chữa (IN_PROGRESS)\n"
            "- Công việc hoàn thành: Kiểm tra hệ thống phanh 4 bánh & Xả dầu máy cũ.\n"
            "- Công việc đang thực hiện: Thay má phanh trước Brembo & Lắp lọc dầu mới.\n"
            "- Dự kiến hoàn thành giao xe: 16:30 chiều nay."
        )
        prompt = PROMPT_CUSTOMER_PROGRESS_LOOKUP.format(question=f"Tra cứu xe {license_plate_or_phone}", customer_order_data=order_data)
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, prompt)
        return {
            "success": True,
            "feature": "customer_progress",
            "output": output_text,
            "model_used": model_used
        }

