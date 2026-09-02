import json
from typing import Dict, Any, List
import httpx

from backend.app.ai.base import AIProvider
from backend.app.ai.validators import wrap_untrusted_data, validate_ai_json_response
from backend.app.ai.providers.fallback import FallbackProvider
from backend.app.config import settings

class OpenAIProvider(AIProvider):
    """Adapter tích hợp OpenAI API (GPT-4o, GPT-3.5)"""

    def __init__(self, api_key: str = None, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.model_name = model_name or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.fallback = FallbackProvider()

    async def summarize_repair_history(
        self, 
        vehicle: Dict[str, Any], 
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.summarize_repair_history(vehicle, history)

        system_prompt = "Bạn là trợ lý ảo Garage VTV. Tóm tắt lịch sử sửa chữa. Trả về đúng JSON schema được yêu cầu."
        user_prompt = f"Thông tin xe:\n{wrap_untrusted_data(vehicle)}\n\nLịch sử:\n{wrap_untrusted_data(history)}"

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[OpenAIProvider Warning] API call failed: {e}. Switching to fallback.")

        return await self.fallback.summarize_repair_history(vehicle, history)

    async def explain_service(
        self, 
        repair_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await self.fallback.explain_service(repair_order)

        system_prompt = "Bạn là trợ lý dịch vụ khách hàng của Garage VTV. Giải thích dịch vụ ngôn ngữ bình dân. Trả về đúng JSON."
        user_prompt = f"Dữ liệu phiếu sửa chữa:\n{wrap_untrusted_data(repair_order)}"

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[OpenAIProvider Warning] API call failed: {e}. Switching to fallback.")

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

        system_prompt = "Bạn là trợ lý lập báo giá cho Garage VTV. Soạn văn phong báo giá nháp. Không đổi giá. Trả về JSON."
        user_prompt = f"Dịch vụ:\n{wrap_untrusted_data(services)}\nPhụ tùng:\n{wrap_untrusted_data(parts)}\nGiá:\n{wrap_untrusted_data(pricing)}"

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[OpenAIProvider Warning] API call failed: {e}. Switching to fallback.")

        return await self.fallback.generate_draft_quotation(services, parts, pricing, vat)
