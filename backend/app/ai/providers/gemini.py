import json
from typing import Dict, Any, List
import httpx

from backend.app.ai.base import AIProvider
from backend.app.ai.validators import wrap_untrusted_data, validate_ai_json_response
from backend.app.ai.providers.fallback import FallbackProvider
from backend.app.config import settings

class GeminiProvider(AIProvider):
    """Adapter tích hợp Google Gemini AI qua REST API / SDK"""

    def __init__(self, api_key: str = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self.model_name = model_name or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        self.fallback = FallbackProvider()

    async def summarize_repair_history(
        self, 
        vehicle: Dict[str, Any], 
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.summarize_repair_history(vehicle, history)

        prompt = f"""
SYSTEM:
Bạn là trợ lý Garage VTV. Nhiệm vụ của bạn là tóm tắt lịch sử sửa chữa được cung cấp.
Chỉ sử dụng thông tin có trong dữ liệu đầu vào. Không được bịa thêm thông tin. Không được tự chẩn đoán lỗi xe.
Nếu dữ liệu thiếu, hãy nói rõ rằng dữ liệu không đủ.
Trả về định dạng JSON thuần túy gồm các trường:
"vehicle_overview": string,
"recent_repair_history": string,
"major_services": list of strings,
"parts_replaced": list of strings,
"repeated_observations": string,
"important_notes": string

USER:
Thông tin xe:
{wrap_untrusted_data(vehicle)}

Lịch sử sửa chữa:
{wrap_untrusted_data(history)}
"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[GeminiProvider Warning] API call failed: {e}. Switching to fallback.")

        return await self.fallback.summarize_repair_history(vehicle, history)

    async def explain_service(
        self, 
        repair_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.explain_service(repair_order)

        prompt = f"""
SYSTEM:
Bạn là trợ lý dịch vụ khách hàng của Garage VTV.
Hãy chuyển thông tin kỹ thuật thành ngôn ngữ dễ hiểu cho khách hàng.
Chỉ giải thích dựa trên dữ liệu được cung cấp. Không được tự chẩn đoán lỗi. Không được thêm dịch vụ, phụ tùng ngoài danh mục.
Trả về định dạng JSON thuần túy gồm:
"title": string,
"simple_explanation": string,
"expected_work": list of strings,
"cost_information": string,
"important_note": string

USER:
Dữ liệu phiếu sửa chữa:
{wrap_untrusted_data(repair_order)}
"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[GeminiProvider Warning] API call failed: {e}. Switching to fallback.")

        return await self.fallback.explain_service(repair_order)

    async def generate_draft_quotation(
        self, 
        services: List[Dict[str, Any]], 
        parts: List[Dict[str, Any]], 
        pricing: Dict[str, Any], 
        vat: float
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.generate_draft_quotation(services, parts, pricing, vat)

        prompt = f"""
SYSTEM:
Bạn là trợ lý lập báo giá cho Garage VTV.
Chỉ sử dụng danh sách dịch vụ và phụ tùng được cung cấp. Không được thay đổi đơn giá do hệ thống cung cấp.
Trả về JSON gồm:
"greeting": string,
"service_summary": string,
"parts_summary": string,
"pricing_note": string,
"warranty_terms": string

USER:
Dịch vụ:
{wrap_untrusted_data(services)}

Phụ tùng:
{wrap_untrusted_data(parts)}

Giá do hệ thống tính (VAT: {vat*100:.0f}%):
{wrap_untrusted_data(pricing)}
"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[GeminiProvider Warning] API call failed: {e}. Switching to fallback.")

        return await self.fallback.generate_draft_quotation(services, parts, pricing, vat)
