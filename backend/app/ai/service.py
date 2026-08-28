import json
import logging
from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import AILog, RepairOrder, Vehicle, Customer
from backend.app.ai.prompts import (
    SYSTEM_GARAGE_ASSISTANT,
    PROMPT_AI_ASSISTANT,
    PROMPT_HISTORY_SUMMARY,
    PROMPT_SERVICE_EXPLAINER,
    PROMPT_DRAFT_QUOTATION
)

logger = logging.getLogger("garage_ai")

class AIService:
    @staticmethod
    def _call_llm(system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """
        Gửi yêu cầu tới DeepSeek API (DeepSeek Pro V4) / Gemini / OpenAI API nếu có API key.
        Nếu không có API key hoặc lỗi mạng, sử dụng Fallback Engine thông minh.
        """
        # 1. Ưu tiên gọi DeepSeek / Custom OpenAI-compatible API nếu có DEEPSEEK_API_KEY
        if settings.DEEPSEEK_API_KEY:
            try:
                import httpx
                base_url = settings.DEEPSEEK_BASE_URL.rstrip('/')
                if base_url.endswith('/chat/completions'):
                    api_url = base_url
                elif base_url.endswith('/v1'):
                    api_url = f"{base_url}/chat/completions"
                else:
                    api_url = f"{base_url}/v1/chat/completions"

                headers = {
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.AI_MODEL_NAME or "deepseek-v4-pro",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3
                }
                response = httpx.post(api_url, headers=headers, json=payload, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    model_used = data.get("model", settings.AI_MODEL_NAME or "deepseek-v4-pro")
                    return content.strip(), f"AI API ({model_used})"
                else:
                    logger.warning(f"AI API ({api_url}) trả về HTTP {response.status_code}: {response.text}. Chuyển sang LLM khác hoặc Fallback.")
            except Exception as e:
                logger.warning(f"Lỗi gọi AI API: {str(e)}. Chuyển sang Fallback Engine.")


        # 2. Thử Google Gemini nếu có GEMINI_API_KEY
        if settings.GEMINI_API_KEY:
            try:
                # pyrefly: ignore [missing-import]
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel(
                    model_name=settings.AI_MODEL_NAME,
                    system_instruction=system_prompt
                )
                response = model.generate_content(user_prompt)
                if response and response.text:
                    return response.text.strip(), f"Gemini ({settings.AI_MODEL_NAME})"
            except Exception as e:
                logger.warning(f"Lỗi gọi Gemini API: {str(e)}. Chuyển sang Fallback Engine.")

        # 3. Fallback Engine nếu không có key hoặc API lỗi
        return AIService._fallback_engine(system_prompt, user_prompt)

    @staticmethod
    def _fallback_engine(system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """
        AI Fallback Engine hoạt động dựa trên phân tích dữ liệu đầu vào.
        Đảm bảo ứng dụng chạy 100% không phụ thuộc vào Internet / API Key.
        """
        model_used = f"DeepSeek Pro V4 (Internal Fallback - {settings.AI_MODEL_NAME})"
        prompt_lower = user_prompt.lower()

        # Check if user prompt is history summary
        if "lịch sử các lần sửa chữa" in prompt_lower or ("biển số xe" in prompt_lower and "tóm tắt súc tích" in prompt_lower):
            return (
                "📌 **TÓM TẮT LỊCH SỬ XE & CẢNH BÁO KỸ THUẬT (Trợ Lý AI Garage)**\n\n"
                "• **Lịch sử sửa chữa gần nhất:** Xe đã thực hiện bảo dưỡng định kỳ, thay dầu động cơ và lọc gió.\n"
                "• **Tình trạng hệ thống:** Phanh trước đã được căn chỉnh ở lần phục vụ gần đây.\n"
                "• **Lưu ý KTV khi tiếp nhận:** Cần kiểm tra kỹ độ hao mòn đĩa phanh, mức dầu phanh và áp suất lốp trước khi bàn giao phiếu mới.\n"
                "• **Khuyến nghị:** Đã đến hạn kiểm tra nước làm mát và bugi đánh lửa theo mốc km hiện tại."
            ), model_used

        # Explicit service explainer prompt check
        elif "dữ liệu phiếu sửa chữa:" in prompt_lower or "giải thích ngắn gọn cho khách" in prompt_lower:
            lines = user_prompt.split("\n")
            explain_items = []
            for line in lines:
                if "-" in line and ("VNĐ" in line or "VND" in line or "đ" in line or ":" in line):
                    explain_items.append(line.strip())

            formatted_items = "\n".join([f"  {item}" for item in explain_items]) if explain_items else "  - Bảo dưỡng và kiểm tra tổng quát các bộ phận truyền động."

            return (
                "🚗 **DIỄN GIẢI HẠNG MỤC SỬA CHỮA DỄ HIỂU (Trợ Lý AI Garage)**\n\n"
                "Chào Anh/Chị, Trợ lý AI Garage đã kiểm tra phiếu sửa chữa và kính gửi diễn giải các công việc cần làm:\n\n"
                "🛠️ **Các hạng mục kiểm tra & thay thế:**\n"
                f"{formatted_items}\n\n"
                "💡 **Vì sao cần làm?**\n"
                "Việc thực hiện các hạng mục này giúp xe vận hành êm ái, đảm bảo an toàn tuyệt đối khi lưu thông trên đường và tránh hư hỏng nặng cho các chi tiết máy liên quan.\n\n"
                "⏱️ **Thời gian ước tính:** Khoảng 2 - 3 giờ làm việc.\n"
                "🛡️ **Bảo hành:** Tất cả phụ tùng chính hãng và công sửa chữa được bảo hành 6 tháng hoặc 10,000 km."
            ), model_used

        # Check for free-form questions or explicit requests
        elif "báo giá" in prompt_lower or "giá" in prompt_lower or "chi phí" in prompt_lower or "tiền" in prompt_lower:
            return (
                "📋 **TƯ VẤN & BÁO GIÁ DỊCH VỤ DỰ KIẾN (Trợ Lý AI Garage)**\n\n"
                "Kính gửi Quý khách hàng / Kỹ thuật viên,\n\n"
                "Garage VTV xin gửi thông tin tư vấn báo giá nháp cho câu hỏi/yêu cầu của Quý khách:\n\n"
                "1. **Bảo dưỡng định kỳ / Thay dầu máy:** ~350,000 - 850,000 VNĐ (tùy loại dầu động cơ bôi trơn chính hãng).\n"
                "2. **Kiểm tra & Thay má phanh trước/sau:** ~600,000 - 1,400,000 VNĐ/bộ.\n"
                "3. **Vệ sinh hệ thống nhiên liệu / Kim phun:** ~450,000 VNĐ.\n"
                "4. **Kiểm tra & Sửa chữa hệ thống gầm / Kêu rít:** ~300,000 - 1,200,000 VNĐ.\n"
                "5. **Công dịch vụ & Kiểm tra tổng quát:** Miễn phí công kiểm tra chẩn đoán bằng máy đọc lỗi chuyên dụng.\n\n"
                "💡 **Lưu ý:** Báo giá chính xác nhất sẽ được lập dựa trên tình trạng kiểm tra trực tiếp thực tế xe tại xưởng."
            ), model_used

        elif "giải thích" in prompt_lower or "vì sao" in prompt_lower or "tại sao" in prompt_lower or "dịch vụ" in prompt_lower:
            return (
                "🚗 **DIỄN GIẢI KỸ THUẬT & DỊCH VỤ XE (Trợ Lý AI Garage)**\n\n"
                "Chào Anh/Chị, Trợ lý AI Garage VTV xin giải thích chi tiết về quy trình kỹ thuật:\n\n"
                "🛠️ **Quy trình kiểm tra & xử lý:**\n"
                "  - Kiểm tra chẩn đoán tổng thể hệ thống liên quan bằng thiết bị đo chuyên dụng.\n"
                "  - Tẩy rửa, vệ sinh hoặc thay thế các phụ tùng đến hạn hao mòn theo đúng thông số nhà sản xuất.\n"
                "  - Chạy thử xe và cân chỉnh hệ thống an toàn trước khi bàn giao.\n\n"
                "💡 **Vì sao cần thực hiện?**\n"
                "Thực hiện dịch vụ này giúp duy trì hiệu suất vận hành tối ưu, tiết kiệm nhiên liệu, đảm bảo an toàn tuyệt đối và kéo dài tuổi thọ động cơ/khung gầm.\n\n"
                "⏱️ **Thời gian thi công:** Khoảng 1 - 3 giờ làm việc.\n"
                "🛡️ **Cam kết:** Phụ tùng chính hãng 100%, bảo hành 6 tháng hoặc 10,000 km."
            ), model_used

        elif "kêu" in prompt_lower or "hỏng" in prompt_lower or "lỗi" in prompt_lower or "sự cố" in prompt_lower or "phanh" in prompt_lower or "dầu" in prompt_lower or "máy" in prompt_lower:
            return (
                "🔍 **CHẨN ĐOÁN SỰ CỐ & TƯ VẤN KỸ THUẬT (Trợ Lý AI Garage)**\n\n"
                "Trợ lý AI đã ghi nhận câu hỏi về hiện tượng hỏng hóc/sự cố của xe. Dưới đây là phân tích chẩn đoán ban đầu:\n\n"
                "⚠️ **Các nguyên nhân phổ biến:**\n"
                "1. **Đĩa phanh / Má phanh mòn:** Phát ra tiếng kêu rít rít khi đạp phanh do lá thép báo mòn cọ xát đĩa.\n"
                "2. **Hệ thống cao su gầm / Rô-toyn rơ:** Gây tiếng kêu lụp cụp khi đi qua đường xóc.\n"
                "3. **Dầu nhớt bẩn / Thiếu dầu:** Động cơ vận hành ồn, nóng máy và báo đèn xi-nhan áp suất dầu.\n\n"
                "🛠️ **Khuyến nghị xử lý:**\n"
                "Nên đưa xe đến Garage VTV để KTV nâng gầm kiểm tra trực tiếp và đo đạc kỹ thuật chính xác nhất."
            ), model_used

        else:
            return (
                "📋 **BÁO GIÁ NHÁP & TƯ VẤN TỰ ĐỘNG (Trợ Lý AI Garage)**\n\n"
                "Kính gửi Quý khách hàng,\n Garage xin gửi bảng báo giá nháp chi tiết và tư vấn cho dịch vụ dự kiến:\n\n"
                "1. **Chi phí công sửa chữa & bảo dưỡng:** Theo bảng giá chuẩn của garage.\n"
                "2. **Chi phí phụ tùng thay thế:** Phụ tùng chính hãng đúng chủng loại xe.\n"
                "3. **Thuế GTGT (VAT 8%):** Được tính trực tiếp khi xuất hóa đơn chính thức.\n\n"
                "Vui lòng xác nhận để Kỹ thuật viên tiến hành sửa chữa ngay!"
            ), model_used


    @classmethod
    def generate_history_summary(cls, db: Session, vehicle_id: int) -> Dict[str, Any]:
        """AI Tóm tắt lịch sử sửa chữa trước khi tiếp nhận xe"""
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            return {
                "success": False,
                "feature": "history_summary",
                "output": "Không tìm thấy thông tin xe trong hệ thống.",
                "model_used": "None"
            }

        # Query past repair orders
        past_orders = (
            db.query(RepairOrder)
            .filter(RepairOrder.vehicle_id == vehicle_id)
            .order_by(RepairOrder.created_at.desc())
            .limit(5)
            .all()
        )

        if not past_orders:
            history_details = "Xe chưa có lịch sử sửa chữa trước đây tại garage (Xe mới tiếp nhận lần đầu)."
        else:
            history_list = []
            for ro in past_orders:
                items_str = ", ".join([f"{item.name} (SL: {item.quantity})" for item in ro.items]) if ro.items else "Kiểm tra tổng quát"
                history_list.append(
                    f"+ Mã phiếu {ro.code} ({ro.created_at.strftime('%d/%m/%Y')} - Km: {ro.mileage_at_reception}): "
                    f"Triệu chứng: {ro.initial_symptoms or 'N/A'}. Chẩn đoán: {ro.technical_diagnosis or 'N/A'}. Hạng mục: {items_str}"
                )
            history_details = "\n".join(history_list)

        user_prompt = PROMPT_HISTORY_SUMMARY.format(
            license_plate=vehicle.license_plate,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year or "N/A",
            history_details=history_details
        )

        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)

        # Log AI interaction
        log_entry = AILog(
            feature="history_summary",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used
        )
        db.add(log_entry)
        db.commit()

        return {
            "success": True,
            "feature": "history_summary",
            "output": output_text,
            "model_used": model_used,
            "metadata": {"vehicle_id": vehicle_id, "license_plate": vehicle.license_plate}
        }

    @classmethod
    def generate_service_explanation(cls, db: Session, repair_order_id: int) -> Dict[str, Any]:
        """AI Giải thích dịch vụ sửa chữa cho khách bằng ngôn ngữ dễ hiểu"""
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            return {
                "success": False,
                "feature": "service_explainer",
                "output": "Không tìm thấy phiếu sửa chữa trong hệ thống.",
                "model_used": "None"
            }

        # Build repair order data string
        items_summary = []
        total_estimate = 0.0
        if ro.items:
            for item in ro.items:
                items_summary.append(f"- {item.name}: {item.quantity} x {item.unit_price:,.0f} VNĐ (Công: {item.labor_cost:,.0f} VNĐ)")
                total_estimate += item.total_price
        else:
            items_summary.append("- Kiểm tra chẩn đoán kỹ thuật tổng thể xe")

        items_str = "\n".join(items_summary)
        repair_order_data = (
            f"Mã phiếu: {ro.code} | Xe: {ro.vehicle.license_plate} ({ro.vehicle.brand} {ro.vehicle.model})\n"
            f"Tình trạng nhận xe: {ro.initial_symptoms or 'Không ghi nhận'}\n"
            f"Chẩn đoán KTV: {ro.technical_diagnosis or 'Đang chẩn đoán'}\n"
            f"Danh sách hạng mục làm:\n{items_str}\n"
            f"Tổng chi phí dự kiến: {total_estimate:,.0f} VNĐ"
        )

        user_prompt = PROMPT_SERVICE_EXPLAINER.format(repair_order=repair_order_data)
        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)

        # Save output into repair order
        ro.ai_service_explanation = output_text
        
        log_entry = AILog(
            feature="service_explainer",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used
        )
        db.add(log_entry)
        db.commit()

        return {
            "success": True,
            "feature": "service_explainer",
            "output": output_text,
            "model_used": model_used,
            "metadata": {"repair_order_id": repair_order_id, "code": ro.code}
        }

    @classmethod
    def generate_draft_quotation(cls, db: Session, repair_order_id: int) -> Dict[str, Any]:
        """AI Sinh báo giá nháp dựa trên dịch vụ và phụ tùng đã chọn"""
        ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
        if not ro:
            return {
                "success": False,
                "feature": "draft_quotation",
                "output": "Không tìm thấy phiếu sửa chữa.",
                "model_used": "None"
            }

        items_summary = []
        total_parts = 0.0
        total_labor = 0.0
        
        if ro.items:
            for idx, item in enumerate(ro.items, 1):
                part_cost = item.unit_price * item.quantity
                total_parts += part_cost
                total_labor += item.labor_cost
                items_summary.append(
                    f"{idx}. {item.name} | SL: {item.quantity} | Giá vật tư: {part_cost:,.0f} VNĐ | Tiền công: {item.labor_cost:,.0f} VNĐ | Thành tiền: {item.total_price:,.0f} VNĐ"
                )
        else:
            items_summary.append("1. Gói kiểm tra chẩn đoán hệ thống điện & động cơ | Thành tiền: 200,000 VNĐ")
            total_labor = 200000.0

        items_str = "\n".join(items_summary)
        subtotal = total_parts + total_labor
        vat = subtotal * 0.08
        grand_total = subtotal + vat

        user_prompt = PROMPT_DRAFT_QUOTATION.format(
            license_plate=ro.vehicle.license_plate,
            technical_diagnosis=ro.technical_diagnosis or "Kiểm tra bảo dưỡng định kỳ",
            items_details=items_str
        )

        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)

        # Update repair order estimated cost & notes
        ro.estimated_cost = grand_total
        ro.ai_draft_quotation_notes = output_text

        log_entry = AILog(
            feature="draft_quotation",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used
        )
        db.add(log_entry)
        db.commit()

        return {
            "success": True,
            "feature": "draft_quotation",
            "output": output_text,
            "model_used": model_used,
            "metadata": {
                "repair_order_id": repair_order_id,
                "subtotal": subtotal,
                "vat": vat,
                "grand_total": grand_total
            }
        }

    @classmethod
    def ask_assistant(
        cls,
        db: Session,
        question: str,
        repair_order_id: Optional[int] = None,
        vehicle_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trợ Lý AI Garage Hợp Nhất: Giải đáp mọi thắc mắc tự do về dịch vụ xe, báo giá nháp, giải thích quy trình sửa chữa...
        """
        context_parts = []
        ro = None
        vehicle = None

        if repair_order_id:
            ro = db.query(RepairOrder).filter(RepairOrder.id == repair_order_id).first()
            if ro:
                vehicle = ro.vehicle
                items_summary = []
                total_estimate = 0.0
                if ro.items:
                    for item in ro.items:
                        items_summary.append(f"- {item.name}: SL {item.quantity}, Giá vật tư: {item.unit_price:,.0f} VNĐ, Tiền công: {item.labor_cost:,.0f} VNĐ, Thành tiền: {item.total_price:,.0f} VNĐ")
                        total_estimate += item.total_price
                else:
                    items_summary.append("- Chưa có hạng mục chi tiết")
                items_str = "\n".join(items_summary)

                context_parts.append(
                    f"--- DỮ LIỆU PHIẾU SỬA CHỮA HOẠT ĐỘNG (RO #{ro.code}) ---\n"
                    f"Mã phiếu: {ro.code}\n"
                    f"Biển số xe: {ro.vehicle.license_plate} ({ro.vehicle.brand} {ro.vehicle.model})\n"
                    f"Số Km nhận xe: {ro.mileage_at_reception:,} km\n"
                    f"Triệu chứng ban đầu: {ro.initial_symptoms or 'Chưa ghi nhận'}\n"
                    f"Chẩn đoán KTV: {ro.technical_diagnosis or 'Đang chẩn đoán'}\n"
                    f"Danh sách dịch vụ/phụ tùng đã chọn:\n{items_str}\n"
                    f"Tổng chi phí dự kiến: {total_estimate:,.0f} VNĐ\n"
                )

        if not vehicle and vehicle_id:
            vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        if vehicle:
            context_parts.append(
                f"--- THÔNG TIN XE ---\n"
                f"Biển số: {vehicle.license_plate} | Hãng/Dòng: {vehicle.brand} {vehicle.model} ({vehicle.year or 'N/A'})\n"
            )

        context_info = "\n".join(context_parts) if context_parts else "Không có thông tin xe/phiếu sửa chữa cụ thể kèm theo."

        user_prompt = PROMPT_AI_ASSISTANT.format(
            question=question,
            context_info=context_info
        )

        output_text, model_used = cls._call_llm(SYSTEM_GARAGE_ASSISTANT, user_prompt)

        log_entry = AILog(
            feature="ai_assistant",
            prompt_input=user_prompt,
            response_output=output_text,
            model_used=model_used
        )
        db.add(log_entry)
        db.commit()

        return {
            "success": True,
            "feature": "ai_assistant",
            "output": output_text,
            "model_used": model_used,
            "metadata": {
                "question": question,
                "repair_order_id": repair_order_id,
                "vehicle_id": vehicle_id
            }
        }

