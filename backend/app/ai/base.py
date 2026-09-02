from abc import ABC, abstractmethod
from typing import Dict, Any, List

class AIProvider(ABC):
    """
    Interface trừu tượng chuẩn mực cho mọi Nhà Cung Cấp AI (AI Provider Interface).
    Mọi adapter (OpenAI, Gemini, Claude, Ollama, Fallback) đều phải tuân thủ hợp đồng này.
    """

    @abstractmethod
    async def summarize_repair_history(
        self, 
        vehicle: Dict[str, Any], 
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Tóm tắt lịch sử bảo dưỡng và cảnh báo hao mòn kỹ thuật."""
        pass

    @abstractmethod
    async def explain_service(
        self, 
        repair_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Chuyển đổi thông tin chẩn đoán kỹ thuật thành lời giải thích bình dân cho khách."""
        pass

    @abstractmethod
    async def generate_draft_quotation(
        self, 
        services: List[Dict[str, Any]], 
        parts: List[Dict[str, Any]], 
        pricing: Dict[str, Any], 
        vat: float
    ) -> Dict[str, Any]:
        """Soạn thảo văn phong và ghi chú báo giá nháp trang trọng."""
        pass
