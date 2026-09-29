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

### Triển khai frontend static + API riêng
Frontend gồm các file HTML/CSS/JS thuần và có thể host trên GitHub Pages, Netlify, Cloudflare Pages hoặc bất kỳ static host nào. Nếu API không cùng domain, sửa `static-config.js`:

```js
window.GARAGE_API_BASE = "https://api.example.com/api/v1";
```

Đồng thời cấu hình `CORS_ORIGINS` ở backend bằng domain frontend cụ thể. Không dùng `*` khi API bật credentials.

### 🔑 Tài khoản và phân quyền (RBAC):
Tài khoản quản trị ban đầu phải được cấu hình bằng các biến môi trường `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_RECEPTIONIST_PASSWORD`, `DEFAULT_TECHNICIAN_PASSWORD` và `DEFAULT_CASHIER_PASSWORD`. Không sử dụng hoặc commit mật khẩu mẫu trong mã nguồn.

---

## 🏗️ 2. KIẾN TRÚC HỆ THỐNG & TÀI LIỆU KỸ THUẬT (DOCUMENTATION)
Toàn bộ tài liệu kỹ thuật hiện hành được đặt trong thư mục [`docs/`](docs/):
- 📘 [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md): Đặc tả yêu cầu, Actor, RBAC Permission Matrix, Sơ đồ Use Case, Sequence Workflow và State Machine.
- 🏛️ [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Kiến trúc Clean Architecture, Layered Services, API-first principles và khả năng di động CSDL.
- 🗄️ [`docs/DATABASE.md`](docs/DATABASE.md): Sơ đồ ERD Mermaid, từ điển dữ liệu, khóa ngoại và chỉ mục.
- 📡 [`docs/API.md`](docs/API.md): Đặc tả RESTful endpoints, request/response schemas và HTTP status codes.
- 🤖 [`docs/AI.md`](docs/AI.md): Kiến trúc AI đa nhà cung cấp, system prompts, khử PII và fallback engine.
- 🛡️ [`docs/SECURITY.md`](docs/SECURITY.md): Phòng chống OWASP Top 10, IDOR, SQL Injection, CSRF/XSS và audit trail.
- 🧪 [`docs/TESTING.md`](docs/TESTING.md): Chiến lược kiểm thử tự động và danh mục test cases.
- 🚀 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Hướng dẫn triển khai Docker Compose, Vercel Serverless và PostgreSQL.
- 📖 [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md): Sổ tay hướng dẫn sử dụng cho các vai trò trong hệ thống.
- 📝 [`docs/SDLC_AI_USAGE.md`](docs/SDLC_AI_USAGE.md): Báo cáo ứng dụng AI trong vòng đời phát triển phần mềm.
- 🎨 [`docs/ui-design-system.md`](docs/ui-design-system.md): Hệ thống thiết kế giao diện.

> Các báo cáo và tài liệu phiên bản cũ được giữ tại [`docs/archive/`](docs/archive/) để tham khảo lịch sử, không dùng làm nguồn thông tin hiện hành.

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
   - Khi SSE không khả dụng, frontend chuyển sang polling API; dữ liệu nghiệp vụ vẫn phải được xác nhận và lưu bởi backend.
