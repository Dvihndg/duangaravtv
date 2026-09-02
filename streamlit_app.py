import os
import sys

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
from datetime import datetime

# Import backend modules safely
try:
    from backend.app.database import SessionLocal, engine
    from backend.app.models import (
        CustomerRequest, Customer, Vehicle, RepairOrder, RepairOrderStatus,
        Invoice, InvoiceStatus, Payment, Part, Service, AILog,
        Quotation, QuotationStatus, Inspection, VehicleReception
    )
    from backend.app.ai.service import AIService
    from backend.app.ai.providers.fallback import FallbackProvider
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False
    DB_ERROR = str(e)

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Garage VTV Engine Pro - Quản Trị & AI Studio",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS Styling (Dark Modern Glassmorphism) ───────────────────────────
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #080e1a;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1329 0%, #060a14 100%) !important;
        border-right: 1px solid #1e293b;
        min-width: 250px !important;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .metric-value {
        color: #38bdf8;
        font-size: 1.75rem;
        font-weight: 800;
        margin-top: 0.35rem;
        font-family: monospace, sans-serif;
    }
    .metric-sub {
        color: #64748b;
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }

    /* Custom Radio Buttons */
    div[data-testid="stRadio"] > div {
        gap: 0.4rem;
    }
    div[data-testid="stRadio"] label {
        background: rgba(15, 23, 42, 0.6);
        padding: 0.55rem 0.85rem;
        border-radius: 8px;
        border: 1px solid #1e293b;
        margin-bottom: 0.1rem;
        transition: all 0.2s;
        font-size: 0.9rem;
        white-space: nowrap !important;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #38bdf8;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.4rem !important;
        white-space: nowrap !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        box-shadow: 0 6px 18px rgba(14, 165, 233, 0.4) !important;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar Header & Navigation ───────────────────────────────────────────────
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=160)
else:
    st.sidebar.title("🚘 GARAGE VTV")

st.sidebar.markdown("<p style='font-size: 0.9rem; font-weight: 700; color: #38bdf8; margin-top: -10px;'>GARAGE VTV ENGINE PRO</p>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='margin: 0.5rem 0 1rem 0; border-color: #1e293b;'/>", unsafe_allow_html=True)

# Concise sidebar menu items that fit on 1 line
menu = st.sidebar.radio(
    "ĐIỀU HƯỚNG",
    [
        "📊 Dashboard & KPIs",
        "🤖 AI Studio & Chẩn Đoán",
        "🛠️ Phiếu Sửa Chữa",
        "📑 Báo Giá & Hóa Đơn",
        "📦 Kho & Phụ Tùng",
        "📋 Yêu Cầu Dịch Vụ"
    ],
    index=1 # Default to AI Studio as the user was exploring it
)

st.sidebar.markdown("<hr style='margin: 1rem 0; border-color: #1e293b;'/>", unsafe_allow_html=True)
st.sidebar.markdown("""
<div style='background: rgba(15, 23, 42, 0.7); border: 1px solid #1e293b; border-radius: 8px; padding: 0.8rem; font-size: 0.78rem;'>
    <div style='color: #38bdf8; font-weight: 700;'>⚡ Hệ Thống Sẵn Sàng</div>
    <div style='color: #94a3b8; margin-top: 0.3rem;'>Backend: <b>FastAPI v1.0</b></div>
    <div style='color: #94a3b8;'>AI Engine: <b>Gemini / Fallback</b></div>
    <div style='color: #94a3b8;'>CSDL: <b>Active (3NF)</b></div>
</div>
""", unsafe_allow_html=True)

# Helper function to get database session
def get_db_session():
    if not DB_CONNECTED:
        return None
    return SessionLocal()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: AI STUDIO & CHẨN ĐOÁN
# ═══════════════════════════════════════════════════════════════════════════════
if menu == "🤖 AI Studio & Chẩn Đoán":
    st.markdown("## 🤖 AI Studio & Trung Tâm Chẩn Đoán Thông Minh")
    st.markdown("<p style='color: #94a3b8; margin-top: -10px;'>Hệ sinh thái Trí Tuệ Nhân Tạo chuyên sâu cho dịch vụ ô tô: tư vấn kỹ thuật, tóm tắt lịch sử, dịch thuật ngữ cho khách và soạn báo giá nháp.</p>", unsafe_allow_html=True)

    tab_chat, tab_summary, tab_explain, tab_quote, tab_obd = st.tabs([
        "💬 Tư Vấn & Chẩn Đoán",
        "📜 Tóm Tắt Lịch Sử Xe",
        "🗣️ Dịch Thuật Ngữ Cho Khách",
        "📝 Soạn Báo Giá Nháp",
        "🔍 Tra Cứu Mã OBD-II"
    ])

    db = get_db_session()

    # ── TAB 1: TƯ VẤN & CHẨN ĐOÁN ─────────────────────────────────────────────
    with tab_chat:
        st.markdown("#### 💬 Trợ Lý Tư Vấn Kỹ Thuật & Bắt Bệnh Xe")
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8;'>Bấm chọn câu hỏi mẫu nhanh hoặc nhập triệu chứng thực tế của phương tiện:</p>", unsafe_allow_html=True)

        if "user_prompt" not in st.session_state:
            st.session_state["user_prompt"] = ""

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        if col_q1.button("🚗 Camry 2018 giật ga", use_container_width=True):
            st.session_state["user_prompt"] = "Xe Toyota Camry 2018 bị giật và rung lắc nhẹ khi tăng ga ở dải tốc độ 40-60 km/h, không báo đèn check engine. Nguyên nhân và cách xử lý?"
            st.rerun()
        if col_q2.button("⚠️ Mazda CX-5 báo ABS", use_container_width=True):
            st.session_state["user_prompt"] = "Xe Mazda CX-5 2020 báo đèn ABS và đèn chống trơn trượt trên bảng đồng hồ khi đi trời mưa. Cần kiểm tra những gì?"
            st.rerun()
        if col_q3.button("❄️ Vios điều hòa nóng", use_container_width=True):
            st.session_state["user_prompt"] = "Toyota Vios 2021 điều hòa lúc mát lúc không, khi đỗ xe thì thổi gió nóng, chạy nhanh thì mát. Nguyên nhân do đâu?"
            st.rerun()
        if col_q4.button("🔧 Bảo dưỡng 40,000 km", use_container_width=True):
            st.session_state["user_prompt"] = "Chi tiết các hạng mục và vật tư cần thay thế ở mốc bảo dưỡng lớn 40,000 km cho xe Hyundai Tucson máy xăng?"
            st.rerun()

        prompt_q = st.text_area(
            "Triệu chứng hoặc câu hỏi:",
            value=st.session_state["user_prompt"],
            placeholder="Ví dụ: Xe SantaFe 2021 máy dầu khó nổ vào buổi sáng, có khói trắng thoát ra từ ống xả...",
            height=100
        )

        col_btn, _ = st.columns([2, 3])
        with col_btn:
            ask_clicked = st.button("🚀 Phân Tích & Chẩn Đoán Ngay", use_container_width=True)

        if ask_clicked:
            if prompt_q.strip():
                st.session_state["last_prompt"] = prompt_q
                with st.spinner("AI Engine đang đối soát CSDL kỹ thuật & phân tích triệu chứng..."):
                    try:
                        res = AIService.ask_assistant(db, question=prompt_q)
                        ai_text = res.get("output") or res.get("answer") or "Đã ghi nhận yêu cầu chẩn đoán kỹ thuật."
                        st.markdown(f"""
                        <div class="ai-box">
                            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #1e293b; padding-bottom: 0.6rem; margin-bottom: 0.8rem;">
                                <div style="font-weight: 700; color: #38bdf8; font-size: 1.05rem;">🎯 KẾT QUẢ PHÂN TÍCH KỸ THUẬT TỪ AI</div>
                                <span class="badge badge-success">ĐỘ CHÍNH XÁC CAO (TOP-1)</span>
                            </div>
                            <div style="font-size: 0.95rem; line-height: 1.6; color: #e2e8f0; white-space: pre-wrap;">
{ai_text}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if res.get("suggested_services"):
                            st.markdown("##### 💡 Phương Án Dịch Vụ & Phụ Tùng Đề Xuất Tại Xưởng:")
                            s_cols = st.columns(len(res["suggested_services"]))
                            for idx, srv in enumerate(res["suggested_services"]):
                                with s_cols[idx % len(s_cols)]:
                                    st.markdown(f"""
                                    <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 8px; padding: 0.8rem; height: 100%;">
                                        <div style="color: #38bdf8; font-weight: 600; font-size: 0.88rem;">{srv.get('name')}</div>
                                        <div style="color: #94a3b8; font-size: 0.78rem; margin-top: 0.3rem;">{srv.get('reason')}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    except Exception as ex:
                        st.error(f"Lỗi phân tích: {ex}")
            else:
                st.warning("Vui lòng nhập triệu chứng xe trước khi bấm chẩn đoán!")

    # ── TAB 2: TÓM TẮT LỊCH SỬ XE ─────────────────────────────────────────────
    with tab_summary:
        st.markdown("#### 📜 Tóm Tắt Lịch Sử Sửa Chữa & Cảnh Báo Hao Mòn")
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8;'>Hệ thống tự động quét toàn bộ các lần bảo dưỡng trước đây để KTV nắm rõ tình trạng xe trước khi nhận:</p>", unsafe_allow_html=True)

        if db:
            vehicles = db.query(Vehicle).all()
            if vehicles:
                veh_options = {f"{v.license_plate} - {v.brand} {v.model} ({v.current_mileage:,} km)": v.id for v in vehicles}
                selected_veh_str = st.selectbox("Chọn xe cần tra cứu lịch sử:", list(veh_options.keys()))
                selected_veh_id = veh_options[selected_veh_str]

                if st.button("🤖 Tóm Tắt Lịch Sử Xe Này", key="btn_summary"):
                    with st.spinner("AI đang tổng hợp dữ liệu lịch sử các lần sửa chữa..."):
                        res_sum = AIService.generate_history_summary(db, selected_veh_id)
                        out_sum = res_sum.get("summary") or res_sum.get("output", "")
                        st.markdown(f"""
                        <div class="ai-box">
                            <div style="font-weight: 700; color: #38bdf8; margin-bottom: 0.6rem;">📋 BẢNG TỔNG KẾT LỊCH SỬ PHƯƠNG TIỆN</div>
                            <div style="font-size: 0.95rem; line-height: 1.6; color: #f1f5f9;">
                                {out_sum}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Chưa có phương tiện nào trong CSDL.")

    # ── TAB 3: GIẢI THÍCH DỊCH VỤ DỄ HIỂU ────────────────────────────────────
    with tab_explain:
        st.markdown("#### 🗣️ Dịch Thuật Ngữ Kỹ Thuật Sang Ngôn Ngữ Dễ Hiểu Cho Khách")
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8;'>Chuyển đổi kết quả chẩn đoán kỹ thuật thành lời giải thích bình dân, lịch sự để gửi qua Zalo / SMS cho chủ xe:</p>", unsafe_allow_html=True)

        if db:
            ros = db.query(RepairOrder).order_by(RepairOrder.id.desc()).all()
            if ros:
                ro_options = {f"{ro.code} - {ro.vehicle.license_plate if ro.vehicle else 'N/A'} ({ro.initial_symptoms or 'Bảo dưỡng'})": ro.id for ro in ros}
                selected_ro_str = st.selectbox("Chọn Phiếu Sửa Chữa:", list(ro_options.keys()), key="sb_explain")
                selected_ro_id = ro_options[selected_ro_str]

                if st.button("✨ Tạo Bản Giải Thích Cho Khách", key="btn_explain"):
                    with st.spinner("AI đang chuyển đổi ngôn ngữ kỹ thuật sang ngôn ngữ bình dân..."):
                        res_exp = AIService.generate_service_explanation(db, selected_ro_id)
                        out_exp = res_exp.get("explanation") or res_exp.get("output", "")
                        st.markdown(f"""
                        <div class="ai-box">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                                <div style="font-weight: 700; color: #34d399;">💬 BẢN GIẢI THÍCH DÀNH CHO CHỦ XE</div>
                                <span class="badge badge-info">SẴN SÀNG GỬI ZALO</span>
                            </div>
                            <div style="font-size: 0.95rem; line-height: 1.6; color: #f1f5f9;">
                                {out_exp}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Chưa có phiếu sửa chữa nào.")

    # ── TAB 4: SOẠN BÁO GIÁ NHÁP ──────────────────────────────────────────────
    with tab_quote:
        st.markdown("#### 📝 Hỗ Trợ Soạn Thảo Báo Giá Nháp")
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8;'>Hệ thống lấy giá từ Server Backend và AI tự động soạn văn phong trang trọng kèm điều khoản bảo hành:</p>", unsafe_allow_html=True)

        if db:
            ros_q = db.query(RepairOrder).order_by(RepairOrder.id.desc()).all()
            if ros_q:
                ro_q_options = {f"{ro.code} - {ro.vehicle.license_plate if ro.vehicle else 'N/A'} - Dự toán: {ro.final_cost or ro.estimated_cost:,.0f} VNĐ": ro.id for ro in ros_q}
                sel_ro_q_str = st.selectbox("Chọn Phiếu Sửa Chữa Cần Báo Giá:", list(ro_q_options.keys()), key="sb_quote")
                sel_ro_q_id = ro_q_options[sel_ro_q_str]

                if st.button("📄 Soạn Báo Giá Nháp Ngay", key="btn_quote"):
                    with st.spinner("Đang tính toán tài chính server-side và tạo thư báo giá..."):
                        res_q = AIService.generate_draft_quotation(db, sel_ro_q_id)
                        out_q = res_q.get("quotation_draft") or res_q.get("output", "")
                        st.markdown(f"""
                        <div class="ai-box">
                            <div style="font-weight: 700; color: #fbbf24; margin-bottom: 0.6rem;">📑 THƯ BÁO GIÁ DỰ TOÁN TRANG TRỌNG</div>
                            <div style="font-size: 0.95rem; line-height: 1.6; color: #f1f5f9;">
                                {out_q}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # ── TAB 5: TRA CỨU OBD-II ────────────────────────────────────────────────
    with tab_obd:
        st.markdown("#### 🔍 Tra Cứu Mã Lỗi Tiêu Chuẩn OBD-II")
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8;'>Nhập mã lỗi chuẩn quét từ máy chẩn đoán (Launch, Autel, G-Scan) để xem phân tích chi tiết:</p>", unsafe_allow_html=True)

        col_obd1, col_obd2 = st.columns([1, 2])
        with col_obd1:
            obd_input = st.text_input("Mã lỗi OBD-II:", value="P0300", placeholder="VD: P0300, P0420, P0171...")
            obd_car = st.text_input("Dòng xe:", value="Toyota Camry 2.5Q 2018")
            btn_obd = st.button("Tra Cứu Mã Lỗi", use_container_width=True)

        with col_obd2:
            if btn_obd or obd_input:
                code = obd_input.upper().strip()
                obd_db = {
                    "P0300": {
                        "name": "Random/Multiple Cylinder Misfire Detected",
                        "vi": "Phát hiện bỏ lửa ngẫu nhiên trên nhiều xi-lanh",
                        "causes": ["Bugi hoặc bô-bin đánh lửa hỏng", "Kim phun nhiên liệu bị nghẹt hoặc bẩn", "Áp suất bơm xăng yếu", "Hở cổ hút khí nạp"],
                        "action": "Kiểm tra bugi, đo điện trở bô-bin, vệ sinh kim phun và đo áp suất buồng đốt."
                    },
                    "P0420": {
                        "name": "Catalyst System Efficiency Below Threshold (Bank 1)",
                        "vi": "Hiệu suất bộ chuyển đổi xúc tác khí xả dưới ngưỡng cho phép",
                        "causes": ["Bầu lọc xúc tác (Catalytic Converter) bị chai hoặc nghẹt", "Cảm biến oxy phía sau bầu xúc tác bị hỏng", "Rò rỉ đường ống xả"],
                        "action": "Kiểm tra điện áp cảm biến oxy số 2, nội soi bầu xúc tác, thay thế cảm biến nếu chập chờn."
                    },
                    "P0171": {
                        "name": "System Too Lean (Bank 1)",
                        "vi": "Hỗn hợp nhiên liệu quá nghèo xăng (Thừa không khí)",
                        "causes": ["Cảm biến lưu lượng khí nạp (MAF) bám bụi bẩn", "Rò rỉ ống chân không hoặc gioăng cổ hút", "Bơm xăng tụt áp, lọc xăng nghẹt"],
                        "action": "Vệ sinh cảm biến MAF bằng dung dịch chuyên dụng, xịt khói tìm điểm rò rỉ chân không."
                    }
                }
                info = obd_db.get(code, {
                    "name": f"DTC Diagnostic Trouble Code {code}",
                    "vi": f"Mã lỗi kỹ thuật hệ thống {code}",
                    "causes": ["Cần kết nối máy chẩn đoán chuyên dụng để đọc luồng dữ liệu Data Stream", "Cảm biến liên quan hoặc đường truyền dây dẫn bị gián đoạn"],
                    "action": "Tiến hành đo kiểm điện trở và xung tín hiệu thực tế trên xe."
                })

                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 10px; padding: 1.2rem;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #f43f5e;">⚠️ MÃ LỖI: {code}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.2rem;">{info['name']}</div>
                    <div style="color: #38bdf8; font-weight: 600; margin-top: 0.5rem;">Ý nghĩa: {info['vi']}</div>
                    <div style="margin-top: 0.8rem; font-weight: 600; color: #e2e8f0;">Các nguyên nhân khả dĩ:</div>
                    <ul style="color: #cbd5e1; font-size: 0.88rem; margin-top: 0.3rem;">
                        {''.join([f'<li>{c}</li>' for c in info['causes']])}
                    </ul>
                    <div style="margin-top: 0.6rem; padding: 0.6rem; background: rgba(56, 189, 248, 0.1); border-left: 3px solid #38bdf8; border-radius: 4px; font-size: 0.85rem;">
                        <b>Khuyến nghị sửa chữa:</b> {info['action']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    if db: db.close()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: TỔNG QUAN & DASHBOARD KPIS
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📊 Dashboard & KPIs":
    st.markdown("## 📊 Tổng Quan Vận Hành & Báo Cáo Doanh Thu")
    st.markdown("<p style='color: #94a3b8; margin-top: -10px;'>Chỉ số thời gian thực kết nối trực tiếp CSDL Garage VTV.</p>", unsafe_allow_html=True)

    db = get_db_session()
    if db:
        try:
            ro_total = db.query(RepairOrder).count()
            ro_in_repair = db.query(RepairOrder).filter(RepairOrder.status.in_([RepairOrderStatus.IN_REPAIR, RepairOrderStatus.WAITING_PARTS, RepairOrderStatus.INSPECTING])).count()
            cust_count = db.query(Customer).count()
            veh_count = db.query(Vehicle).count()
            
            invoices = db.query(Invoice).all()
            total_rev = sum([inv.total_amount for inv in invoices if inv.total_amount])
            paid_rev = sum([inv.paid_amount for inv in invoices if inv.paid_amount])
            debt_rev = sum([inv.balance_due for inv in invoices if inv.balance_due])
            
            low_stock = db.query(Part).filter(Part.stock_quantity <= Part.min_stock_alert).count()

            # 4 Key Metrics
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">💰 Tổng Doanh Thu</div>
                    <div class="metric-value">{total_rev:,.0f} đ</div>
                    <div class="metric-sub">Đã thu: {paid_rev:,.0f} đ</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🚘 Xe Đang Nằm Xưởng</div>
                    <div class="metric-value">{ro_in_repair}</div>
                    <div class="metric-sub">Tổng tích lũy: {ro_total} lượt xe</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">👥 Khách Hàng & Xe</div>
                    <div class="metric-value">{cust_count} / {veh_count}</div>
                    <div class="metric-sub">{veh_count} phương tiện đăng ký</div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">⚠️ Cảnh Báo Tồn Kho</div>
                    <div class="metric-value" style="color: {'#f43f5e' if low_stock > 0 else '#10b981'};">{low_stock} mã</div>
                    <div class="metric-sub">Dưới định mức tối thiểu</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)

            # Charts
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.markdown("##### 📈 Phân Bố Trạng Thái Phiếu Sửa Chữa")
                ros = db.query(RepairOrder).all()
                if ros:
                    df_ro = pd.DataFrame([{"Trạng Thái": str(r.status.value if hasattr(r.status, 'value') else r.status).upper()} for r in ros])
                    fig_pie = px.pie(
                        df_ro, names="Trạng Thái", hole=0.45,
                        color_discrete_sequence=["#38bdf8", "#10b981", "#f59e0b", "#f43f5e", "#a855f7"]
                    )
                    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1", margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_pie, use_container_width=True)

            with col_ch2:
                st.markdown("##### 📦 Top Phụ Tùng Tồn Kho Dồi Dào Nhất")
                parts = db.query(Part).order_by(Part.stock_quantity.desc()).limit(8).all()
                if parts:
                    df_p = pd.DataFrame([{"Tên": p.name[:25], "Tồn": p.stock_quantity} for p in parts])
                    fig_bar = px.bar(
                        df_p, x="Tồn", y="Tên", orientation="h",
                        color="Tồn", color_continuous_scale="Blues"
                    )
                    fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1", margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_bar, use_container_width=True)

        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: PHIẾU SỬA CHỮA
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "🛠️ Phiếu Sửa Chữa":
    st.markdown("## 🛠️ Danh Sách Phiếu Sửa Chữa & Tiến Độ Xưởng")

    db = get_db_session()
    if db:
        try:
            ros = db.query(RepairOrder).order_by(RepairOrder.id.desc()).all()
            if ros:
                ro_list = []
                for ro in ros:
                    plate = ro.vehicle.license_plate if ro.vehicle else "N/A"
                    brand = f"{ro.vehicle.brand} {ro.vehicle.model}" if ro.vehicle else ""
                    tech_name = ro.technician.full_name if ro.technician else "Chưa giao"
                    st_val = str(ro.status.value if hasattr(ro.status, 'value') else ro.status).upper()
                    
                    ro_list.append({
                        "Mã RO": ro.code,
                        "Biển Số": plate,
                        "Dòng Xe": brand,
                        "Kỹ Thuật Viên": tech_name,
                        "Triệu Chứng Khách Báo": ro.initial_symptoms or ro.customer_complaint or "Bảo dưỡng",
                        "Trạng Thái": st_val,
                        "Chi Phí Dự Toán": f"{ro.final_cost or ro.estimated_cost:,.0f} đ",
                        "Ngày Vào": ro.created_at.strftime("%d/%m/%Y") if ro.created_at else ""
                    })
                df_ro = pd.DataFrame(ro_list)
                
                # Filters
                col_s, col_f = st.columns([3, 1])
                with col_s:
                    kw = st.text_input("🔍 Tìm kiếm theo Mã RO, Biển số hoặc Dòng xe:")
                with col_f:
                    st_filter = st.selectbox("Lọc Trạng Thái:", ["Tất Cả"] + sorted(list(df_ro["Trạng Thái"].unique())))

                filtered_df = df_ro
                if kw:
                    filtered_df = filtered_df[
                        filtered_df["Mã RO"].str.contains(kw, case=False, na=False) |
                        filtered_df["Biển Số"].str.contains(kw, case=False, na=False) |
                        filtered_df["Dòng Xe"].str.contains(kw, case=False, na=False)
                    ]
                if st_filter != "Tất Cả":
                    filtered_df = filtered_df[filtered_df["Trạng Thái"] == st_filter]

                st.dataframe(filtered_df, use_container_width=True, height=450)
            else:
                st.info("Chưa có phiếu sửa chữa nào.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: BÁO GIÁ & HÓA ĐƠN
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📑 Báo Giá & Hóa Đơn":
    st.markdown("## 📑 Quản Lý Báo Giá & Hóa Đơn Thanh Toán")

    tab_inv, tab_quo = st.tabs(["💰 Hóa Đơn & Thanh Toán", "📄 Báo Giá Dịch Vụ"])
    db = get_db_session()
    if db:
        try:
            with tab_inv:
                invoices = db.query(Invoice).order_by(Invoice.id.desc()).all()
                if invoices:
                    inv_data = []
                    for inv in invoices:
                        inv_data.append({
                            "Mã Hóa Đơn": inv.invoice_number,
                            "Mã Phiếu RO": inv.repair_order.code if inv.repair_order else "N/A",
                            "Biển Số": inv.repair_order.vehicle.license_plate if (inv.repair_order and inv.repair_order.vehicle) else "N/A",
                            "Tiền Trước Thuế": f"{inv.subtotal:,.0f} đ",
                            "VAT (10%)": f"{inv.vat or inv.tax_amount:,.0f} đ",
                            "Tổng Hóa Đơn": f"{inv.total_amount:,.0f} đ",
                            "Đã Thu": f"{inv.paid_amount:,.0f} đ",
                            "Còn Nợ": f"{inv.balance_due:,.0f} đ",
                            "Trạng Thái": str(inv.status.value if hasattr(inv.status, 'value') else inv.status).upper()
                        })
                    st.dataframe(pd.DataFrame(inv_data), use_container_width=True, height=400)
                else:
                    st.info("Chưa có hóa đơn nào.")

            with tab_quo:
                quos = db.query(Quotation).order_by(Quotation.id.desc()).all()
                if quos:
                    quo_data = []
                    for q in quos:
                        quo_data.append({
                            "Mã Báo Giá": q.quotation_code,
                            "Mã Phiếu RO": q.repair_order.code if q.repair_order else "N/A",
                            "Tiền Công & Linh Kiện": f"{q.subtotal:,.0f} đ",
                            "Chiết Khấu": f"{q.discount:,.0f} đ",
                            "VAT 10%": f"{q.vat:,.0f} đ",
                            "Tổng Giá Trị": f"{q.total:,.0f} đ",
                            "Trạng Thái": str(q.status.value if hasattr(q.status, 'value') else q.status).upper(),
                            "Hạn Duyệt": q.valid_until.strftime("%d/%m/%Y") if q.valid_until else "Không thời hạn"
                        })
                    st.dataframe(pd.DataFrame(quo_data), use_container_width=True, height=400)
                else:
                    st.info("Chưa có báo giá nào.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: KHO & PHỤ TÙNG
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📦 Kho & Phụ Tùng":
    st.markdown("## 📦 Quản Lý Kho Phụ Tùng & Danh Mục Dịch Vụ")

    t_part, t_serv = st.tabs(["📦 50+ Phụ Tùng Thay Thế", "🔧 20+ Dịch Vụ Kỹ Thuật"])
    db = get_db_session()
    if db:
        try:
            with t_part:
                parts = db.query(Part).order_by(Part.id.asc()).all()
                if parts:
                    p_data = []
                    for p in parts:
                        is_low = p.stock_quantity <= p.min_stock_alert
                        p_data.append({
                            "Mã Kho": p.code,
                            "Tên Phụ Tùng": p.name,
                            "Thương Hiệu": p.brand or "Chính hãng",
                            "Đơn Giá Bán": f"{p.unit_price:,.0f} đ",
                            "Giá Vốn": f"{p.cost_price:,.0f} đ",
                            "Tồn Kho": p.stock_quantity,
                            "Định Mức Cảnh Báo": p.min_stock_alert,
                            "Tình Trạng": "⚠️ Sắp hết" if is_low else "🟢 Dồi dào"
                        })
                    st.dataframe(pd.DataFrame(p_data), use_container_width=True, height=480)
                else:
                    st.info("Kho trống.")

            with t_serv:
                services = db.query(Service).order_by(Service.id.asc()).all()
                if services:
                    s_data = [{
                        "Mã Dịch Vụ": s.code,
                        "Tên Dịch Vụ": s.name,
                        "Phân Loại": s.category,
                        "Tiền Công Chuẩn": f"{s.labor_cost:,.0f} đ",
                        "Thời Gian Dự Kiến": f"{s.estimated_hours} giờ"
                    } for s in services]
                    st.dataframe(pd.DataFrame(s_data), use_container_width=True, height=480)
                else:
                    st.info("Chưa có dịch vụ nào.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: YÊU CẦU DỊCH VỤ
# ═══════════════════════════════════════════════════════════════════════════════
elif menu == "📋 Yêu Cầu Dịch Vụ":
    st.markdown("## 📋 Quản Lý Yêu Cầu Đặt Lịch Từ Khách Hàng")

    db = get_db_session()
    if db:
        try:
            reqs = db.query(CustomerRequest).order_by(CustomerRequest.id.desc()).all()
            if reqs:
                req_data = [{
                    "Mã Yêu Cầu": r.request_code,
                    "Khách Hàng": r.full_name,
                    "Số Điện Thoại": r.phone,
                    "Biển Số": r.license_plate,
                    "Dòng Xe": f"{r.vehicle_brand} {r.vehicle_model}",
                    "Gói Dịch Vụ": r.service_type,
                    "Ngày Gửi": r.created_at.strftime("%H:%M %d/%m/%Y") if r.created_at else "",
                    "Trạng Thái": r.status.value if hasattr(r.status, 'value') else str(r.status)
                } for r in reqs]
                st.dataframe(pd.DataFrame(req_data), use_container_width=True, height=450)
            else:
                st.info("Chưa có yêu cầu đặt lịch nào từ khách hàng.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()
