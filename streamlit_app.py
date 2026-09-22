import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GarageAI Dashboard", page_icon="🚗", layout="wide")

st.title("🚗 Dashboard Quản Trị GarageAI (Streamlit)")
st.markdown("---")

def get_db_connection():
    conn = sqlite3.connect('backend/garage.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()

# Lấy dữ liệu KPI
today = datetime.now().strftime("%Y-%m-%d")
this_month = datetime.now().strftime("%Y-%m")

cur = conn.cursor()

# 1. Xe đang sửa (status = 'in_progress')
cur.execute("SELECT COUNT(*) as count FROM repair_orders WHERE status = 'in_progress'")
ro_in_progress = cur.fetchone()['count']

# 2. Lịch hẹn hôm nay
cur.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date LIKE ?", (f"{today}%",))
appointments_today = cur.fetchone()['count']

# 3. Doanh thu tháng này
cur.execute("SELECT SUM(total_amount) as total FROM invoices WHERE invoice_date LIKE ? AND status = 'paid'", (f"{this_month}%",))
revenue_this_month = cur.fetchone()['total'] or 0

# 4. Khách hàng mới tháng này
cur.execute("SELECT COUNT(*) as count FROM customers WHERE created_at LIKE ?", (f"{this_month}%",))
new_customers = cur.fetchone()['count']

# Hiển thị KPI
col1, col2, col3, col4 = st.columns(4)
col1.metric("Xe Đang Sửa", f"{ro_in_progress} xe")
col2.metric("Lịch Hẹn Hôm Nay", f"{appointments_today} lịch")
col3.metric("Doanh Thu Tháng Này", f"{revenue_this_month:,.0f} VNĐ")
col4.metric("Khách Mới (Tháng)", f"{new_customers} người")

st.markdown("---")

st.subheader("📈 Doanh Thu 6 Tháng Gần Nhất")
cur.execute("""
    SELECT strftime('%Y-%m', invoice_date) as month, SUM(total_amount) as revenue
    FROM invoices
    WHERE status = 'paid'
    GROUP BY strftime('%Y-%m', invoice_date)
    ORDER BY month DESC
    LIMIT 6
""")
rows = cur.fetchall()
if rows:
    df_rev = pd.DataFrame(rows, columns=['month', 'revenue'])
    df_rev = df_rev.sort_values(by='month')
    df_rev.set_index('month', inplace=True)
    st.line_chart(df_rev)
else:
    st.info("Chưa có dữ liệu doanh thu.")

st.markdown("---")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🔧 Phiếu Sửa Chữa Gần Đây")
    df_orders = pd.read_sql_query("SELECT code, status, estimated_cost, created_at FROM repair_orders ORDER BY created_at DESC LIMIT 5", conn)
    st.dataframe(df_orders, use_container_width=True)

with col_b:
    st.subheader("🔔 Hoạt Động Mới Nhất")
    df_reqs = pd.read_sql_query("SELECT request_code, full_name, service_type, created_at FROM customer_requests ORDER BY created_at DESC LIMIT 5", conn)
    st.dataframe(df_reqs, use_container_width=True)

conn.close()
