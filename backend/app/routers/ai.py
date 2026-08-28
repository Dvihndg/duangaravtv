# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    AIAssistantRequest, AIHistorySummaryRequest, AIServiceExplainerRequest, AIDraftQuotationRequest, AIResponse
)
from backend.app.auth import get_current_user
from backend.app.ai.service import AIService

router = APIRouter(prefix="/api/v1/ai", tags=["AI Engine"])

@router.post("/assistant", response_model=AIResponse)
def ask_ai_assistant(
    req: AIAssistantRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trợ Lý AI Garage Hợp Nhất: Giải đáp thắc mắc tự do về dịch vụ xe, kỹ thuật ô tô, báo giá nháp & giải thích quy trình.
    """
    res = AIService.ask_assistant(
        db,
        question=req.question,
        repair_order_id=req.repair_order_id,
        vehicle_id=req.vehicle_id
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["output"])
    return res


@router.post("/summarize-history", response_model=AIResponse)
def summarize_vehicle_history(
    req: AIHistorySummaryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    AI Chức năng 1: Tóm tắt lịch sử sửa chữa của xe trước khi tiếp nhận
    """
    res = AIService.generate_history_summary(db, req.vehicle_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["output"])
    return res

@router.post("/explain-services", response_model=AIResponse)
def explain_services_to_customer(
    req: AIServiceExplainerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    AI Chức năng 2: Sinh giải thích dịch vụ sửa chữa cho khách hàng bằng ngôn ngữ dễ hiểu
    (Sử dụng đúng Prompt System: 'Bạn là trợ lý garage ô tô. Chỉ giải thích dựa trên dữ liệu sửa chữa được cung cấp...')
    """
    res = AIService.generate_service_explanation(db, req.repair_order_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["output"])
    return res

@router.post("/draft-quotation", response_model=AIResponse)
def generate_draft_quotation(
    req: AIDraftQuotationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    AI Chức năng 3: Sinh báo giá nháp dựa trên dịch vụ và phụ tùng đã chọn
    """
    res = AIService.generate_draft_quotation(db, req.repair_order_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["output"])
    return res
