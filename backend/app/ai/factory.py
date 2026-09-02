from backend.app.ai.base import AIProvider
from backend.app.ai.providers.gemini import GeminiProvider
from backend.app.ai.providers.openai import OpenAIProvider
from backend.app.ai.providers.ollama import OllamaProvider
from backend.app.ai.providers.fallback import FallbackProvider
from backend.app.config import settings

def get_ai_provider() -> AIProvider:
    """Factory khởi tạo AIProvider tương ứng với cấu hình biến môi trường AI_PROVIDER"""
    provider_name = getattr(settings, "AI_PROVIDER", "fallback").lower()
    
    if provider_name == "openai" and getattr(settings, "OPENAI_API_KEY", ""):
        return OpenAIProvider()
    elif provider_name == "gemini" and getattr(settings, "GEMINI_API_KEY", ""):
        return GeminiProvider()
    elif provider_name == "ollama":
        return OllamaProvider()
    
    # Mặc định an toàn: Fallback Provider (chạy mượt mà offline không phụ thuộc mạng)
    return FallbackProvider()
