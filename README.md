# 🚘 HỆ THỐNG QUẢN LÝ GARAGE VTV TÍCH HỢP AI (GARAGE VTV AI MANAGEMENT SYSTEM)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20SQLite-336791.svg)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Container-Docker%20Compose-2496ED.svg)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Hệ thống Quản lý Vận hành Toàn diện cho Chuỗi Garage Ô tô kết hợp Trí Tuệ Nhân Tạo (AI Engine). Hệ thống quản lý khép kín luồng nghiệp vụ:
**Khách hàng → Phương tiện → Lịch hẹn → Tiếp nhận xe → Khảo sát & Chẩn đoán → Phiếu sửa chữa → Phân công KTV → Dịch vụ & Phụ tùng → Báo giá → Khách duyệt → Sửa chữa → Nghiệm thu KCS → Hóa đơn → Thanh toán → Hoàn thành → Lịch sử bảo dưỡng → Báo cáo BI**.

---

## 🌐 1. ĐỊA CHỈ TRUY CẬP VẬN HÀNH (LIVE PRODUCTION)
- **Cổng thông tin Khách hàng (Public Portal)**: [https://duangaravtv.vercel.app/](https://duangaravtv.vercel.app/) (Không cần đăng nhập).
- **Khu vực Quản trị Nội bộ (Internal Admin)**: [https://duangaravtv.vercel.app/admin](https://duangaravtv.vercel.app/admin).
- **Tài liệu API Tự động (Swagger UI)**: [https://duangaravtv.vercel.app/docs](https://duangaravtv.vercel.app/docs).

### 🔑 Tài khoản Thử nghiệm 4 Vai trò (RBAC):
| Vai trò | Tên đăng nhập | Mật khẩu | Quyền hạn chính |
|---|---|---|---|
| **Quản lý (Manager)** | `admin` | `admin123` | Toàn quyền cấu hình, xem báo cáo doanh thu, audit logs, AI logs, xóa mềm |
| **Lễ tân (Receptionist)** | `letan` | `letan123` | Tiếp nhận xe, đặt lịch hẹn, tạo báo giá, gửi khách duyệt, tra cứu tiến độ |
| **Kỹ thuật viên (Technician)** | `kythuat` | `tech123` | Thực hiện chẩn đoán, đề xuất phụ tùng, cập nhật tiến độ xe được giao (IDOR safe) |
| **Thu ngân (Cashier)** | `thungan` | `cashier123` | Lập hóa đơn từ RO, ghi nhận thanh toán (tiền mặt / chuyển khoản), in hóa đơn |

---

## 🏗️ 2. KIẾN TRÚC HỆ THỐNG & TÀI LIỆU KỸ THUẬT (DOCUMENTATION)
Toàn bộ tài liệu thiết kế chi tiết được đặt trong thư mục [`docs/`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs):
- 📘 [`docs/REQUIREMENTS.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/REQUIREMENTS.md): Đặc tả yêu cầu, Actor, RBAC Permission Matrix, Sơ đồ Use Case, Sequence Workflow và State Machine.
- 🏛️ [`docs/ARCHITECTURE.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/ARCHITECTURE.md): Kiến trúc Clean Architecture, Layered Services, API-first principles và khả năng di động CSDL.
- 🗄️ [`docs/DATABASE.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/DATABASE.md): Sơ đồ ERD Mermaid, Từ điển dữ liệu Data Dictionary 18 bảng chuẩn 3NF, Khóa ngoại và Chỉ mục.
- 📡 [`docs/API.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/API.md): Đặc tả toàn diện các RESTful Endpoints, Request/Response JSON schemas và HTTP Status Codes.
- 🤖 [`docs/AI.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/AI.md): Kiến trúc AI đa nhà cung cấp, System Prompts, Thẻ `<UNTRUSTED_DATA>`, Khử PII và Fallback Engine.
- 🛡️ [`docs/SECURITY.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/SECURITY.md): Phòng chống OWASP Top 10, IDOR, SQL Injection, CSRF/XSS và Audit Trail.
- 🧪 [`docs/TESTING.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/TESTING.md): Chiến lược kiểm thử tự động, danh mục 17 Test Cases bắt buộc (TC01 - TC17).
- 🚀 [`docs/DEPLOYMENT.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/DEPLOYMENT.md): Hướng dẫn triển khai Docker Compose, Vercel Serverless và Supabase PostgreSQL.
- 📖 [`docs/USER_GUIDE.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/USER_GUIDE.md): Sổ tay hướng dẫn sử dụng cho Khách hàng, Lễ tân, Kỹ thuật viên, Thu ngân và Quản lý.
- 📝 [`docs/SDLC_AI_USAGE.md`](file:///c:/Users/Duong%20Ngan/OneDrive/Desktop/demotesthethong/docs/SDLC_AI_USAGE.md): Báo cáo ứng dụng AI trong cả 4 giai đoạn vòng đời phát triển phần mềm.

---

## ⚡ 3. KHỞI CHẠY BẰNG DOCKER & DOCKER COMPOSE

Chạy toàn bộ hệ thống (FastAPI Backend + PostgreSQL + Redis) chỉ với 1 câu lệnh duy nhất:
```bash
# 1. Khởi tạo tệp môi trường
cp .env.example .env

# 2. Xây dựng và khởi chạy container
docker compose up -d --build

# 3. Nạp dữ liệu mẫu vào CSDL container
docker compose exec backend python seed_data.py
```
- Truy cập Cổng khách hàng: `http://localhost:8000`
- Truy cập Swagger API Docs: `http://localhost:8000/docs`

---

## 💻 4. KHỞI CHẠY CỤC BỘ (LOCAL DEVELOPMENT)

### Bước 1: Cài đặt thư viện phụ thuộc
```powershell
pip install -r requirements.txt
```

### Bước 2: Nạp dữ liệu mẫu phong phú
Tạo 22+ khách hàng, 32+ xe, 20+ dịch vụ, 50+ phụ tùng kho, 30+ phiếu sửa chữa, báo giá và hóa đơn:
```powershell
python seed_data.py
```

### Bước 3: Chạy Kiểm thử tự động 17 Test Cases (TC01 - TC17)
```powershell
pytest backend/tests/test_master_suite.py -v
```

### Bước 4: Khởi động máy chủ phát triển
- **FastAPI Server**:
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- **Streamlit Analytics Dashboard (Giao diện Quản trị Chuyên sâu)**:
```powershell
python -m streamlit run streamlit_app.py
```

---

## 🔒 5. QUY TẮC AN TOÀN & BẢO VỆ TÀI CHÍNH BẤT BIẾN
1. **Server-Side Financial Authority**:
   - `subtotal = sum(labor + parts)`
   - `vat = (subtotal - discount) * vat_rate`
   - `total = (subtotal - discount) + vat`
   - Tuyệt đối không bao giờ tin tưởng số tiền client gửi lên.
2. **Strict State Machine**:
   - Vòng đời phiếu sửa chữa tuân thủ chặt chẽ: `RECEIVED` → `INSPECTING` → `QUOTATION_PENDING` → `WAITING_CUSTOMER_APPROVAL` → `APPROVED` → `IN_REPAIR` → `QUALITY_CHECK` → `COMPLETED`.
   - Không cho phép nhảy cóc trạng thái trái phép.
3. **No Negative Stock**:
   - Tồn kho phụ tùng không bao giờ được phép âm (`stock >= 0`). Giao dịch xuất kho được thực hiện với khóa hàng kiểm soát chặt chẽ.
4. **No Overpayment**:
   - Số tiền thanh toán không được vượt quá số dư còn lại của hóa đơn (`amount <= balance_due`).
   - Hóa đơn đã HỦY (`CANCELLED`) tuyệt đối không nhận thanh toán.
5. **Prompt Injection & PII Protection**:
   - Mọi dữ liệu do người dùng nhập được bọc trong thẻ `<UNTRUSTED_DATA>...</UNTRUSTED_DATA>`.
   - Toàn bộ thông tin cá nhân (SĐT, Email) được khử định danh trước khi gửi tới API bên ngoài.
   - Khi mạng gián đoạn, **Smart Offline Fallback Engine** tự động kích hoạt bảo đảm hoạt động 24/7.
