import os
import sys

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import backend modules safely
try:
    from backend.app.database import SessionLocal, engine
    from backend.app.models import CustomerRequest, Customer, Vehicle, RepairOrder, Invoice, SparePart, Service, AILog
    from backend.app.ai.service import AIService
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False
    DB_ERROR = str(e)

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Garage VTV Engine Pro - Streamlit Admin Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS Styling ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark / Cyberpunk Premium Styling */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    .css-1d384fe, [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #38bdf8;
        font-size: 1.8rem;
        font-weight: 800;
        margin-top: 0.25rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.25rem;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar Header & Navigation ───────────────────────────────────────────────
st.sidebar.image("logo.png", width=180) if os.path.exists("logo.png") else st.sidebar.title("🚘 GARAGE VTV")
st.sidebar.markdown("### **Hệ Thống Quản Lý Garage Tích Hợp AI**")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "📌 **Danh Mục Quản Trị**",
    [
        "📊 Tổng Quan & Dashboard KPIs",
        "📋 Quản Lý Yêu Cầu Dịch Vụ",
        "🛠️ Phiếu Sửa Chữa & Chẩn Đoán",
        "📦 Kho Phụ Tùng & Dịch Vụ",
        "🤖 Trợ Lý AI Garage Engine"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Garage VTV Engine Pro** v2.5\nChạy trên nền tảng Streamlit + FastAPI + Gemini AI")

# Helper function to get database session
def get_db_session():
    if not DB_CONNECTED:
        return None
    return SessionLocal()

# ─── MODULE 1: TỔNG QUAN & DASHBOARD ──────────────────────────────────────────
if menu == "📊 Tổng Quan & Dashboard KPIs":
    st.title("📊 Tổng Quan Vận Hành Garage VTV")
    st.markdown("Hệ thống báo cáo chỉ số vận hành real-time kết nối CSDL PostgreSQL/SQLite.")

    db = get_db_session()
    if db:
        try:
            req_count = db.query(CustomerRequest).count()
            ro_count = db.query(RepairOrder).count()
            active_ros = db.query(RepairOrder).filter(RepairOrder.status.in_(["received", "diagnosing", "in_progress"])).count()
            cust_count = db.query(Customer).count()
            invoices = db.query(Invoice).all()
            total_rev = sum([inv.total_amount for inv in invoices if inv.total_amount])
            low_stock = db.query(SparePart).filter(SparePart.stock_quantity <= SparePart.min_stock_alert).count()

            # KPI Grid
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🚘 Xe Đang Sửa Tại Xưởng</div>
                    <div class="metric-value">{active_ros}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📋 Tổng Yêu Cầu Tiếp Nhận</div>
                    <div class="metric-value">{req_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">💰 Tổng Doanh Thu Hóa Đơn</div>
                    <div class="metric-value">{total_rev:,.0f} VNĐ</div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">⚠️ Cảnh Báo Tồn Kho Thấp</div>
                    <div class="metric-value" style="color: #f43f5e;">{low_stock}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Charts section
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("📈 Trạng Thái Yêu Cầu Dịch Vụ")
                reqs = db.query(CustomerRequest).all()
                if reqs:
                    df_req = pd.DataFrame([{"Trạng Thái": r.status} for r in reqs])
                    fig = px.pie(df_req, names="Trạng Thái", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Chưa có yêu cầu dịch vụ nào để hiển thị biểu đồ.")

            with col_chart2:
                st.subheader("🛠️ Thống Kê Phụ Tùng Tồn Kho")
                parts = db.query(SparePart).all()
                if parts:
                    df_parts = pd.DataFrame([{"Tên Phụ Tùng": p.name, "Số Lượng Tồn": p.stock_quantity} for p in parts])
                    fig_bar = px.bar(df_parts, x="Tên Phụ Tùng", y="Số Lượng Tồn", color="Số Lượng Tồn", color_continuous_scale="Viridis")
                    fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Kho phụ tùng chưa có dữ liệu.")

        except Exception as ex:
            st.error(f"Lỗi truy vấn CSDL: {ex}")
        finally:
            db.close()
    else:
        st.warning("CSDL chưa sẵn sàng hoặc đang ở chế độ Offline.")

# ─── MODULE 2: QUẢN LÝ YÊU CẦU DỊCH VỤ ───────────────────────────────────────
elif menu == "📋 Quản Lý Yêu Cầu Dịch Vụ":
    st.title("📋 Quản Lý Yêu Cầu Đặt Lịch Dịch Vụ")
    st.markdown("Xem danh sách yêu cầu dịch vụ do Khách hàng điền từ Cổng Khách Hàng.")

    db = get_db_session()
    if db:
        try:
            reqs = db.query(CustomerRequest).order_by(CustomerRequest.id.desc()).all()
            if reqs:
                data = []
                for r in reqs:
                    data.append({
                        "ID": r.id,
                        "Mã Yêu Cầu": r.request_code,
                        "Họ và Tên": r.full_name,
                        "Số Điện Thoại": r.phone,
                        "Biển Số Xe": r.license_plate,
                        "Hãng/Mẫu Xe": f"{r.vehicle_brand} {r.vehicle_model}",
                        "Dịch Vụ Yêu Cầu": r.service_name,
                        "Ngày Gửi": r.created_at.strftime("%H:%M - %d/%m/%Y") if r.created_at else "",
                        "Trạng Thái": r.status
                    })
                df = pd.DataFrame(data)

                # Filter bar
                col_f1, col_f2 = st.columns([2, 1])
                with col_f1:
                    search_kw = st.text_input("🔍 Tìm kiếm theo Tên, SĐT hoặc Biển Số Xe:")
                with col_f2:
                    status_filter = st.selectbox("Lọc Trạng Thái:", ["Tất Cả", "Pending", "Confirmed", "In_Progress", "Completed", "Cancelled"])

                if search_kw:
                    df = df[
                        df["Họ và Tên"].str.contains(search_kw, case=False, na=False) |
                        df["Số Điện Thoại"].str.contains(search_kw, case=False, na=False) |
                        df["Biển Số Xe"].str.contains(search_kw, case=False, na=False)
                    ]
                if status_filter != "Tất Cả":
                    df = df[df["Trạng Thái"] == status_filter]

                st.dataframe(df, use_container_width=True)

                # Export option
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Xuất Danh Sách Ra CSV", data=csv, file_name="Customer_Requests.csv", mime="text/csv")
            else:
                st.info("Chưa có yêu cầu dịch vụ nào trong CSDL.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ─── MODULE 3: PHIẾU SỬA CHỮA ────────────────────────────────────────────────
elif menu == "🛠️ Phiếu Sửa Chữa & Chẩn Đoán":
    st.title("🛠️ Phiếu Sửa Chữa & Chẩn Đoán Kỹ Thuật")

    db = get_db_session()
    if db:
        try:
            ros = db.query(RepairOrder).order_by(RepairOrder.id.desc()).all()
            if ros:
                ro_data = []
                for ro in ros:
                    ro_data.append({
                        "ID": ro.id,
                        "Mã Phiếu": ro.code,
                        "Biển Số Xe": ro.vehicle_plate if hasattr(ro, 'vehicle_plate') else "N/A",
                        "Triệu Chứng": ro.initial_symptoms,
                        "Trạng Thái": ro.status,
                        "Tổng Chi Phí": f"{ro.final_cost:,.0f} VNĐ" if ro.final_cost else "0 VNĐ"
                    })
                st.dataframe(pd.DataFrame(ro_data), use_container_width=True)
            else:
                st.info("Chưa có phiếu sửa chữa nào.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ─── MODULE 4: KHO PHỤ TÙNG & DỊCH VỤ ─────────────────────────────────────────
elif menu == "📦 Kho Phụ Tùng & Dịch Vụ":
    st.title("📦 Danh Mục Kho Phụ Tùng & Dịch Vụ")

    tab1, tab2 = st.tabs(["📦 Kho Phụ Tùng", "🔧 Danh Mục Dịch Vụ"])

    db = get_db_session()
    if db:
        try:
            with tab1:
                parts = db.query(SparePart).all()
                if parts:
                    df_p = pd.DataFrame([{
                        "Mã": p.code, "Tên Phụ Tùng": p.name,
                        "Đơn Giá Bán": f"{p.unit_price:,.0f} VNĐ",
                        "Số Lượng Tồn": p.stock_quantity,
                        "Mức Cảnh Báo": p.min_stock_alert
                    } for p in parts])
                    st.dataframe(df_p, use_container_width=True)
                else:
                    st.info("Kho phụ tùng trống.")

            with tab2:
                srvs = db.query(Service).all()
                if srvs:
                    df_s = pd.DataFrame([{
                        "Mã": s.code, "Tên Dịch Vụ": s.name,
                        "Tiền Công": f"{s.labor_cost:,.0f} VNĐ"
                    } for s in srvs])
                    st.dataframe(df_s, use_container_width=True)
                else:
                    st.info("Danh mục dịch vụ trống.")
        except Exception as ex:
            st.error(f"Lỗi: {ex}")
        finally:
            db.close()

# ─── MODULE 5: TRỢ LÝ AI GARAGE ───────────────────────────────────────────────
elif menu == "🤖 Trợ Lý AI Garage Engine":
    st.title("🤖 Trợ Lý AI Chẩn Đoán & Tư Vấn Garage VTV")
    st.markdown("Thử nghiệm các tính năng AI Engine trực tiếp trên giao diện Streamlit.")

    prompt_q = st.text_area("💬 Nhập câu hỏi kỹ thuật hoặc triệu chứng xe ô tô:", placeholder="VD: Xe Camry 2018 bị giật khi tăng tốc và báo lỗi Check Engine...")

    if st.button("🚀 Gửi Câu Hỏi Cho Trợ Lý AI"):
        if prompt_q.strip():
            with st.spinner("AI Engine đang phân tích CSDL & chẩn đoán..."):
                db = get_db_session()
                try:
                    res = AIService.ask_assistant(db, question=prompt_q)
                    st.success("✅ Kết Quả Phân Tích Từ AI Engine:")
                    st.markdown(res.get("answer", "Chưa có phản hồi"))

                    if res.get("suggested_services"):
                        st.subheader("💡 Dịch Vụ Được Đề Xuất:")
                        for srv in res["suggested_services"]:
                            st.write(f"- **{srv.get('name')}**: {srv.get('reason')}")
                except Exception as ex:
                    st.error(f"Lỗi gọi AI Engine: {ex}")
                finally:
                    if db: db.close()
        else:
            st.warning("Vui lòng nhập câu hỏi trước khi gửi!")
