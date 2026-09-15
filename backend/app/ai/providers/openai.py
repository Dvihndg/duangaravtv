import json
from typing import Dict, Any, List, Optional
import httpx

from backend.app.ai.base import AIProvider
from backend.app.ai.validators import wrap_untrusted_data, validate_ai_json_response
from backend.app.ai.providers.fallback import FallbackProvider
from backend.app.config import settings

class OpenAIProvider(AIProvider):
    """Adapter tÃ­ch há»£p OpenAI API (GPT-4o, GPT-3.5)"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
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

        system_prompt = "Báº¡n lÃ  trá»£ lÃ½ áº£o Garage VTV. TÃ³m táº¯t lá»‹ch sá»­ sá»­a chá»¯a. Tráº£ vá» Ä‘Ãºng JSON schema Ä‘Æ°á»£c yÃªu cáº§u."
        user_prompt = f"ThÃ´ng tin xe:\n{wrap_untrusted_data(vehicle)}\n\nLá»‹ch sá»­:\n{wrap_untrusted_data(history)}"

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

        system_prompt = "Báº¡n lÃ  trá»£ lÃ½ dá»‹ch vá»¥ khÃ¡ch hÃ ng cá»§a Garage VTV. Giáº£i thÃ­ch dá»‹ch vá»¥ ngÃ´n ngá»¯ bÃ¬nh dÃ¢n. Tráº£ vá» Ä‘Ãºng JSON."
        user_prompt = f"Dá»¯ liá»‡u phiáº¿u sá»­a chá»¯a:\n{wrap_untrusted_data(repair_order)}"

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

        system_prompt = "Báº¡n lÃ  trá»£ lÃ½ láº­p bÃ¡o giÃ¡ cho Garage VTV. Soáº¡n vÄƒn phong bÃ¡o giÃ¡ nhÃ¡p. KhÃ´ng Ä‘á»•i giÃ¡. Tráº£ vá» JSON."
        user_prompt = f"Dá»‹ch vá»¥:\n{wrap_untrusted_data(services)}\nPhá»¥ tÃ¹ng:\n{wrap_untrusted_data(parts)}\nGiÃ¡:\n{wrap_untrusted_data(pricing)}"

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
