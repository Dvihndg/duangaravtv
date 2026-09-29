from backend.app.ai.prompts import (
    PROMPT_ADMIN_ASSISTANT,
    PROMPT_AI_ASSISTANT,
    SYSTEM_GARAGE_ADMIN_ASSISTANT,
    SYSTEM_GARAGE_ASSISTANT,
)


def test_customer_ai_playbook_covers_common_question_families():
    required = [
        "Dịch vụ/bảo dưỡng",
        "Giá/báo giá",
        "Đặt/hủy/đổi lịch",
        "Tình trạng/tiến độ đơn",
        "Triệu chứng kỹ thuật",
        "Bảo hành/đổi trả",
        "Hóa đơn/thanh toán",
        "Khiếu nại/CSKH",
    ]
    for phrase in required:
        assert phrase in SYSTEM_GARAGE_ASSISTANT
    assert "an toàn → trạng thái xe → chi phí" in PROMPT_AI_ASSISTANT


def test_admin_ai_playbook_covers_periods_lookups_bi_and_injection():
    required = [
        "Ngày: dùng đúng ngày",
        "Tháng/quý/năm",
        "Khoảng ngày",
        "So sánh",
        "Đa biến",
        "Bất thường/dự báo",
        "Tra cứu hóa đơn/đơn hàng",
        "Tra cứu tồn kho",
        "Tra cứu lịch hẹn",
        "Tra cứu khách hàng",
        "Prompt injection",
    ]
    for phrase in required:
        assert phrase in SYSTEM_GARAGE_ADMIN_ASSISTANT
    assert "không yêu cầu người dùng bổ sung" in PROMPT_ADMIN_ASSISTANT
