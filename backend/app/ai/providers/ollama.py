import json
from typing import Dict, Any, List
import httpx

from backend.app.ai.base import AIProvider
from backend.app.ai.validators import wrap_untrusted_data, validate_ai_json_response
from backend.app.ai.providers.fallback import FallbackProvider
from backend.app.config import settings

class OllamaProvider(AIProvider):
    """Adapter tích hợp Local LLM qua Ollama (Llama 3, Mistral, Qwen 2.5)"""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", base_url) or base_url
        self.model_name = getattr(settings, "OLLAMA_MODEL", model_name) or model_name
        self.fallback = FallbackProvider()

    async def summarize_repair_history(
        self, 
        vehicle: Dict[str, Any], 
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        prompt = f"""
Bạn là trợ lý Garage VTV. Tóm tắt lịch sử sửa chữa sau đây và trả về JSON thuần túy:
{wrap_untrusted_data(vehicle)}
{wrap_untrusted_data(history)}
"""
        try:
            payload = {"model": self.model_name, "prompt": prompt, "format": "json", "stream": False}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    text = res.json()["response"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[OllamaProvider Warning] Call failed: {e}. Switching to fallback.")

        return await self.fallback.summarize_repair_history(vehicle, history)

    async def explain_service(
        self, 
        repair_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = f"""
Bạn là trợ lý dịch vụ khách hàng Garage VTV. Giải thích chẩn đoán thành ngôn ngữ bình dân. Trả về JSON:
{wrap_untrusted_data(repair_order)}
"""
        try:
            payload = {"model": self.model_name, "prompt": prompt, "format": "json", "stream": False}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    text = res.json()["response"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[OllamaProvider Warning] Call failed: {e}. Switching to fallback.")

        return await self.fallback.explain_service(repair_order)

    async def generate_draft_quotation(
        self, 
        services: List[Dict[str, Any]], 
        parts: List[Dict[str, Any]], 
        pricing: Dict[str, Any], 
        vat: float
    ) -> Dict[str, Any]:
        prompt = f"""
Bạn là trợ lý lập báo giá Garage VTV. Soạn văn phong báo giá nháp. Không đổi giá. Trả về JSON:
Dịch vụ: {wrap_untrusted_data(services)}
Phụ tùng: {wrap_untrusted_data(parts)}
Giá: {wrap_untrusted_data(pricing)}
"""
        try:
            payload = {"model": self.model_name, "prompt": prompt, "format": "json", "stream": False}
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    text = res.json()["response"]
                    return validate_ai_json_response(text)
        except Exception as e:
            print(f"[OllamaProvider Warning] Call failed: {e}. Switching to fallback.")

        return await self.fallback.generate_draft_quotation(services, parts, pricing, vat)
