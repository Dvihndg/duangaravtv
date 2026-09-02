from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AILog, User, UserRole
from backend.app.schemas import (
    AIAssistantRequest, AIHistorySummaryRequest, AIServiceExplainerRequest, AIDraftQuotationRequest, AIResponse,
    AIEvaluationMetricsResponse, DemoScenarioResponse, AITechnicalTroubleshootRequest, AIOBDDiagnosticRequest,
    AIBusinessAnalysisRequest, AIPredictiveMaintenanceRequest, AICustomerProgressRequest
)
from backend.app.auth import get_current_user, require_roles
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
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("output", "Lỗi AI"))
    return res

@router.post("/summarize-history", response_model=AIResponse)
@router.post("/history-summary", response_model=AIResponse)
def summarize_vehicle_history(
    req: AIHistorySummaryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    AI Chức năng 1: Tóm tắt lịch sử sửa chữa của xe trước khi tiếp nhận
    """
    res = AIService.generate_history_summary(db, req.vehicle_id)
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("output", "Lỗi AI"))
    return res

@router.post("/explain-services", response_model=AIResponse)
@router.post("/service-explanation", response_model=AIResponse)
def explain_services_to_customer(
    req: AIServiceExplainerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    AI Chức năng 2: Sinh giải thích dịch vụ sửa chữa cho khách hàng bằng ngôn ngữ dễ hiểu
    """
    res = AIService.generate_service_explanation(db, req.repair_order_id)
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("output", "Lỗi AI"))
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
    if not res.get("success", False):
        raise HTTPException(status_code=400, detail=res.get("output", "Lỗi AI"))
    return res

@router.get("/logs")
def list_ai_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER]))
):
    """Lấy danh sách nhật ký gọi AI logs (Chỉ dành cho Manager)"""
    return db.query(AILog).order_by(AILog.created_at.desc()).limit(limit).all()

@router.post("/demo-scenarios/{scenario_id}", response_model=DemoScenarioResponse)
def trigger_demo_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if scenario_id < 1 or scenario_id > 5:
        raise HTTPException(status_code=400, detail="Mã kịch bản demo phải từ 1 đến 5.")
    return run_demo_scenario(db, scenario_id)

@router.get("/evaluation-report", response_model=AIEvaluationMetricsResponse)
def get_ai_evaluation_report(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return generate_ai_evaluation_report(db)

@router.post("/technical-troubleshoot", response_model=AIResponse)
def analyze_technical_troubleshoot(
    req: AITechnicalTroubleshootRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return AIService.analyze_technical_troubleshooting(db, req.symptoms, req.car_model)

@router.post("/obd-diagnostic", response_model=AIResponse)
def analyze_obd_diagnostic(
    req: AIOBDDiagnosticRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return AIService.analyze_obd_fault(db, req.brand, req.model, req.year, req.mileage, req.symptoms, req.obd_code)

@router.post("/business-intelligence", response_model=AIResponse)
def analyze_business_intelligence(
    req: AIBusinessAnalysisRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return AIService.analyze_business_performance(db, req.question)

@router.post("/predictive-maintenance", response_model=AIResponse)
def predict_vehicle_maintenance(
    req: AIPredictiveMaintenanceRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return AIService.predict_maintenance(db, req.license_plate)

@router.post("/customer-progress", response_model=AIResponse)
def lookup_customer_progress(
    req: AICustomerProgressRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return AIService.lookup_customer_vehicle_progress(db, req.license_plate_or_phone)
