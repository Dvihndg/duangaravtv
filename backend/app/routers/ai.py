# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    AIAssistantRequest, AIHistorySummaryRequest, AIServiceExplainerRequest, AIDraftQuotationRequest, AIResponse,
    AIEvaluationMetricsResponse, DemoScenarioResponse
)
from backend.app.auth import get_current_user
from backend.app.ai.service import AIService
from backend.app.ai.scenarios import run_demo_scenario
from backend.app.ai.benchmark import generate_ai_evaluation_report

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

@router.post("/demo-scenarios/{scenario_id}", response_model=DemoScenarioResponse)
def trigger_demo_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Thực thi 5 Kịch bản Demo cho Bài báo cáo bảo vệ dự án Garage AI (Nhóm VTV).
    """
    if scenario_id < 1 or scenario_id > 5:
        raise HTTPException(status_code=400, detail="Mã kịch bản demo phải từ 1 đến 5.")
    return run_demo_scenario(db, scenario_id)

@router.get("/evaluation-report", response_model=AIEvaluationMetricsResponse)
def get_ai_evaluation_report(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Bước 11: Đo lường & Báo cáo Đánh giá (Top-1 Accuracy, Parts Precision, Price Variance = 0%, Latency, Token Costs).
    """
    return generate_ai_evaluation_report(db)

