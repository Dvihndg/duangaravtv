# Báo Cáo Hệ Thống Toàn Diện
## Garage VTV Engine Pro — Hệ thống Quản lý Garage Ô tô Tích hợp AI

**Phiên bản:** 2.0  
**Ngày cập nhật:** 18/09/2026  
**Người lập báo cáo:** AI Antigravity (Tự động sinh từ phân tích codebase)

---

## 1. Tổng Quan Dự Án

**Garage VTV Engine Pro** là hệ thống quản lý garage ô tô toàn diện dành cho chuỗi garage quy mô vừa. Hệ thống cho phép quản lý lịch hẹn, phiếu sửa chữa, kho phụ tùng, hóa đơn, khách hàng và tích hợp tư vấn kỹ thuật bằng AI.

### Mục tiêu chính
| Mục tiêu | Mô tả |
|---|---|
| Quản lý vận hành | Toàn bộ luồng từ đặt lịch → tiếp nhận → sửa chữa → xuất hóa đơn |
| Tự động hóa | AI tư vấn kỹ thuật, đặt lịch online, tra cứu tiến độ xe |
| Đa vai trò | RBAC 4 cấp nội bộ + cổng khách hàng tự phục vụ |
| Offline first | Hoạt động ngay cả khi không có backend (LocalStorage Engine) |
| Realtime | SSE stream cập nhật dashboard không cần refresh |

---

## 2. Kiến Trúc Hệ Thống

Hệ thống gồm 3 lớp chính:

```
CLIENT LAYER
├── index.html        (Landing Page - Marketing)
├── login.html        (Auth Page)
├── admin.html        (Admin Panel - 9 views, 8 modals)
├── customer.html     (Customer Portal - Tra cứu & đặt lịch)
├── app.js            (Frontend Logic - 3517 dòng, 153KB)
└── styles.css        (Design System - dark/light theme)

BACKEND LAYER - FastAPI
├── main.py           (App Entry Point)
├── auth.py           (JWT Auth)
├── routers/          (14 API Routers)
├── models.py         (SQLAlchemy ORM - 557 dòng)
├── database.py       (SQLite Engine)
├── services/         (Business Logic)
└── ai/               (AI Integration - Google Gemini)

DATA LAYER
├── garage.db         (SQLite Database)
├── localStorage      (Offline Cache - browser)
└── Google Gemini API (AI Engine)
```

### Nguyên tắc thiết kế
- **Offline-first**: Khi backend không phản hồi, `app.js` tự động chuyển sang `localStorage Engine`
- **Fault-tolerant**: Mỗi function khởi tạo được wrap trong try/catch riêng
- **Progressive enhancement**: UI hoạt động ngay cả không có AI/backend

---

## 3. Tech Stack

### Frontend
| Thành phần | Chi tiết |
|---|---|
| **HTML/CSS/JS** | Vanilla — không framework |
| **Font** | Huninn (Google Fonts), Plus Jakarta Sans, Outfit |
| **Icons** | Font Awesome 6.4.0 |
| **Date picker** | Flatpickr + Vietnamese locale |
| **Charts** | Chart.js 4.4.3 (bar/line charts) |
| **Realtime** | Server-Sent Events (SSE) |
| **Auth** | JWT token stored in localStorage |
| **Offline DB** | localStorage JSON engine |

### Backend
| Thành phần | Chi tiết |
|---|---|
| **Framework** | FastAPI (Python) |
| **ORM** | SQLAlchemy |
| **Database** | SQLite (`garage.db`) |
| **Auth** | python-jose + bcrypt (JWT) |
| **AI** | Google Gemini API |
| **Server** | Uvicorn ASGI |
| **Config** | python-dotenv |

### DevOps & Deployment
| Thành phần | Chi tiết |
|---|---|
| **Containerization** | Docker + docker-compose.yml |
| **CI/CD** | GitHub Actions (`.github/`) |
| **Cloud Deploy** | Railway (`railway.toml`) / Vercel (`vercel.json`) |
| **Python version** | 3.11 (`.python-version`) |

---

## 4. Cấu Trúc Thư Mục

```
demotesthethong/
├── admin.html              # Trang quản trị nội bộ (9 views, 8 modals)
├── customer.html           # Cổng tra cứu & đặt lịch khách hàng
├── index.html              # Landing page (1018 dòng)
├── login.html              # Trang đăng nhập
├── app.js                  # Frontend logic toàn bộ (3517 dòng, 153KB)
├── styles.css              # Design system (1642 dòng, dark/light theme)
├── booking-success.css     # CSS riêng cho trang xác nhận booking
├── logo.png                # Logo thương hiệu
├── schema.txt              # SQL schema export (155KB)
│
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app entry, CORS, startup events
│   │   ├── models.py       # SQLAlchemy models (557 dòng)
│   │   ├── database.py     # DB engine + session factory
│   │   ├── auth.py         # JWT helper functions
│   │   ├── config.py       # App settings & env vars
│   │   ├── routers/        # 14 API route handlers
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic layer
│   │   └── ai/             # AI integration module
│   └── tests/              # Pytest test suite
│
├── api/
│   └── index.py            # Vercel serverless adapter
│
├── docs/                   # Tài liệu kỹ thuật
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   ├── REQUIREMENTS.md
│   ├── SECURITY.md
│   ├── TESTING.md
│   ├── USER_GUIDE.md
│   └── SYSTEM_REPORT.md    # (file này)
│
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 5. Database Schema

### Các bảng chính

| Bảng | Mô tả | Cột quan trọng |
|---|---|---|
| `users` | Tài khoản nội bộ | id, username, email, hashed_password, role |
| `customers` | Khách hàng | id, full_name, phone, email, customer_code |
| `vehicles` | Xe của khách | id, customer_id, license_plate, brand, model, year, current_mileage |
| `appointments` | Lịch hẹn | id, vehicle_id, appointment_time, status, notes |
| `repair_orders` | Phiếu sửa chữa | id, code, vehicle_id, symptoms, diagnosis, mileage, status, final_cost |
| `ro_items` | Hạng mục phiếu | id, repair_order_id, service_id/part_id, quantity, unit_price |
| `services` | Dịch vụ | id, service_code, name, labor_cost |
| `parts` | Phụ tùng kho | id, part_code, name, sell_price, stock_quantity, min_stock_alert |
| `invoices` | Hóa đơn | id, repair_order_id, subtotal, vat_rate, total_amount, paid_amount, status |
| `payments` | Thanh toán | id, invoice_id, amount, payment_method, payment_date |
| `customer_requests` | Yêu cầu online | id, request_code, full_name, phone, license_plate, service_type, status |

### Enums quan trọng

**RepairOrderStatus** (13 trạng thái):
```
draft → received → inspecting → quotation_pending → waiting_customer_approval 
→ approved → in_repair → waiting_parts → quality_check → completed 
→ finished → invoiced → cancelled
```

**CustomerRequestStatus** (8 trạng thái):
```
Pending → Contacted → Confirmed → InProgress 
→ Completed / Converted / Cancelled / Rejected
```

**UserRole** (4 vai trò nội bộ):
```
manager | receptionist | technician | cashier
```

---

## 6. API Endpoints

### Base URL
- **Local**: `http://127.0.0.1:8000/api/v1`
- **Production**: `/api/v1`

### Danh sách Routers (14 modules)

| Module | Prefix | Mô tả |
|---|---|---|
| Auth | `/auth` | Login, logout, verify token, /me |
| Customers | `/customers` | CRUD khách hàng + xe |
| Appointments | `/appointments` | CRUD lịch hẹn, update status |
| Repair Orders | `/repair-orders` | CRUD phiếu, thêm items, update status |
| Customer Requests | `/customer-requests` | CRUD yêu cầu online, chuyển đổi sang phiếu |
| Inventory | `/inventory` | CRUD dịch vụ + phụ tùng |
| Invoices | `/invoices` | Tạo hóa đơn, thanh toán |
| Quotations | `/quotations` | Báo giá |
| Receptions | `/receptions` | Tiếp nhận xe |
| Analytics | `/analytics` | Dashboard KPI, doanh thu |
| AI | `/ai` | Chat AI, chẩn đoán, báo giá |
| Audit Logs | `/audit-logs` | Lịch sử thay đổi |
| Settings | `/settings` | Cấu hình hệ thống |
| Realtime | `/realtime` | SSE stream |

### Authentication
```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
Body: username=admin&password=[configured via environment]

Response: { "access_token": "eyJ...", "token_type": "bearer" }

# Tất cả admin requests cần:
Authorization: Bearer {access_token}
```

### Ví dụ API chính

```javascript
// Tạo phiếu sửa chữa
POST /api/v1/repair-orders
{
  "vehicle_id": 5,
  "initial_symptoms": "Xe kêu tiếng lạ ở bánh trước trái",
  "mileage_at_reception": 45000
}

// Thêm item vào phiếu
POST /api/v1/repair-orders/{id}/items
{
  "item_type": "service",   // "service" | "part"
  "item_id": 3,
  "quantity": 1
}

// Tạo yêu cầu đặt lịch (PUBLIC - không cần auth)
POST /api/v1/customer-requests
{
  "fullName": "Nguyễn Văn A",
  "phone": "0333442358",
  "licensePlate": "51H-888.88",
  "vehicleBrand": "Toyota",
  "vehicleModel": "Camry",
  "serviceType": "Bảo dưỡng định kỳ",
  "description": "Xe đi 45,000 km, muốn thay nhớt và kiểm tra phanh"
}

// AI chat
POST /api/v1/ai/chat
{
  "message": "Xe Toyota Camry 2.5Q đi 45,000 km cần làm gì?",
  "context": { "repair_order_id": null, "vehicle_id": null }
}
```

---

## 7. Phân Quyền & Vai Trò (RBAC)

### Ma trận quyền hạn

| Module | Manager | Receptionist | Technician | Cashier | Customer |
|---|:---:|:---:|:---:|:---:|:---:|
| Dashboard KPI | ✅ Full | ✅ Limited | ❌ | ❌ | ❌ |
| Lịch hẹn | ✅ CRUD | ✅ CRUD | 👁 View | ❌ | 👁 Own |
| Phiếu sửa chữa | ✅ CRUD | ✅ Create | ✅ Update | 👁 View | ❌ |
| Khách hàng & Xe | ✅ CRUD | ✅ CRUD | 👁 View | 👁 View | 👁 Own |
| Kho phụ tùng | ✅ CRUD | 👁 View | ✅ Update | 👁 View | ❌ |
| Hóa đơn | ✅ CRUD | ❌ | ❌ | ✅ CRUD | 👁 Own |
| Thanh toán | ✅ Full | ❌ | ❌ | ✅ CRUD | ❌ |
| Quản lý yêu cầu | ✅ Full | ✅ Full | 👁 View | ❌ | 📝 Submit |
| AI Chat | ✅ | ✅ | ✅ | ❌ | ✅ |
| Cài đặt hệ thống | ✅ | ❌ | ❌ | ❌ | ❌ |

### Tài khoản demo
| Vai trò | Username | Password |
|---|---|---|
| Manager (Admin) | `admin` | `[configured via environment]` |
| Receptionist | `letan` | `[configured via environment]` |
| Technician | `kythuat` | `[configured via environment]` |
| Cashier | `thungan` | `[configured via environment]` |

---

## 8. Các Trang & Views UI

### 8.1 `index.html` — Landing Page
- Hero section với CTA đặt lịch
- Giới thiệu dịch vụ, combo bảo dưỡng
- Tra cứu tiến độ xe theo biển số
- AI tư vấn floating modal
- Responsive, dark/light mode

### 8.2 `login.html` — Đăng Nhập Nội Bộ
- Form đăng nhập username/password
- JWT token lưu localStorage
- Redirect về `admin.html` sau login
- Guard: block customer/unknown roles

### 8.3 `admin.html` — Trang Quản Trị (9 views)

| View ID | Tên | Mô tả |
|---|---|---|
| `view-dashboard` | Dashboard | 4 KPI cards, Chart.js revenue chart, activity feed, recent ROs |
| `view-appointments` | Lịch Hẹn | CRUD lịch hẹn, 4 KPI, filter/search, date picker |
| `view-repair-orders` | Phiếu Sửa Chữa | Danh sách phiếu, filter by status, modal chi tiết |
| `view-customer-requests` | Quản Lý Yêu Cầu | Yêu cầu online từ khách, 4 KPI, chuyển phiếu sửa chữa |
| `view-customers` | Khách Hàng & Xe | Danh sách, CRUD, tìm kiếm |
| `view-inventory` | Kho & Dịch Vụ | 2 bảng: dịch vụ + phụ tùng |
| `view-invoices` | Hóa Đơn | Danh sách hóa đơn, modal thanh toán VietQR |
| `view-ai-studio` | AI Quản Trị | Chat inline với AI Engine |
| `view-customer-portal` | Đăng Ký Khách | Form đăng ký + xác nhận 5-step |

**8 Modals trong admin.html:**
- `modal-ai-result` — AI tư vấn floating
- `modal-phone-contact` — Hotline popup với callback form
- `modal-new-appointment` — Tạo lịch hẹn
- `modal-new-ro` — Tiếp nhận xe, tạo phiếu
- `modal-ro-detail` — Chi tiết phiếu, thêm items, chẩn đoán AI
- `modal-new-customer` — Thêm khách hàng + xe
- `modal-payment` — Thanh toán hóa đơn + VietQR Techcombank
- `modal-new-service` / `modal-new-part` — Thêm danh mục

### 8.4 `customer.html` — Cổng Khách Hàng
- Tra cứu tiến độ sửa xe theo biển số / mã REQ
- Form đặt lịch dịch vụ online
- AI tư vấn kỹ thuật
- Xem dịch vụ, combo bảo dưỡng, bảng giá

---

## 9. Luồng Nghiệp Vụ Chính

### Luồng đầy đủ: Đặt lịch → Sửa chữa → Thanh toán

```
KHÁCH HÀNG
  ↓ Điền form đặt lịch (customer.html)
  ↓ POST /customer-requests
  → Nhận mã REQ-YYYYMMDD-XXXX

LỄ TÂN (admin.html → view-customer-requests)
  ↓ Thấy yêu cầu mới (badge notification)
  ↓ Xem chi tiết → Gọi xác nhận khách
  ↓ PATCH /customer-requests/{id}/status (Contacted)
  ↓ POST /customer-requests/{id}/convert-to-reception
  → Tạo Repair Order tự động

KỸ THUẬT VIÊN (admin.html → view-repair-orders)
  ↓ Nhận phiếu sửa chữa
  ↓ Điền chẩn đoán kỹ thuật
  ↓ Hỏi AI: "Xe Toyota Camry 2.5Q, 45,000km cần gì?"
  ↓ Thêm dịch vụ + phụ tùng vào phiếu
  ↓ PATCH /repair-orders/{id}/status (completed)

THU NGÂN (admin.html → view-invoices)
  ↓ Tạo hóa đơn từ phiếu
  ↓ POST /invoices
  ↓ Chọn phương thức thanh toán (tiền mặt / VietQR)
  ↓ POST /invoices/{id}/payments
  → Invoice paid ✅, phiếu status = invoiced
```

### Luồng Offline (LocalStorage Engine)
```
1. app.js gọi API → timeout 6 giây
2. isBackendAvailable = false
3. apiFetch() → getOfflineMockResponse()
4. Đọc/ghi localStorage với keys vtv_db_*
5. Khi backend online → tự chuyển về online mode
6. Auto-create customers & vehicles khi submit request
7. Anti-spam: cùng SĐT + biển số trong 60s bị block
```

---

## 10. AI Integration

### Điểm tích hợp trong UI
| Vị trí | Cách dùng |
|---|---|
| Admin → AI Studio | Chat inline với full history |
| Floating button | Mở modal AI bất cứ lúc nào |
| Modal AI result | Popup tư vấn kỹ thuật |
| RO Detail modal | "Trợ Lý AI Garage" — tư vấn theo xe cụ thể |
| Customer Portal | "Hỏi AI Trước" khi đặt lịch |
| Customer page | AI tư vấn cho khách hàng |

### Cấu hình AI
- **Model**: Google Gemini Pro
- **Endpoint**: `POST /api/v1/ai/chat`
- **Timeout**: 45 giây (AI calls), 10 giây (regular calls)
- **Context**: Truyền `repair_order_id` + `vehicle_id` để AI tư vấn theo xe cụ thể

---

## 11. Realtime (SSE)

```javascript
// Khởi tạo SSE stream
const es = new EventSource(`${API_BASE}/realtime/stream`);
es.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Cập nhật badge số yêu cầu mới trên nav
  // Refresh KPI dashboard
  // Notification toast
};
```

**Sự kiện SSE xử lý:**
- `new_customer_request` → Badge update trên sidebar
- `repair_order_updated` → Refresh dashboard
- `payment_received` → Toast notification

---

## 12. Offline Engine Chi Tiết

### localStorage Keys
| Key | Nội dung |
|---|---|
| `vtv_db_customers` | JSON[] khách hàng |
| `vtv_db_vehicles` | JSON[] xe |
| `vtv_db_appointments` | JSON[] lịch hẹn |
| `vtv_db_repair_orders` | JSON[] phiếu sửa |
| `vtv_db_invoices` | JSON[] hóa đơn |
| `vtv_db_customer_requests` | JSON[] yêu cầu đặt lịch |
| `vtv_db_services` | JSON[] dịch vụ |
| `vtv_db_parts` | JSON[] phụ tùng |
| `garage_access_token` | JWT token |
| `garage_user_role` | Role hiện tại |
| `garage_theme` | `dark` / `light` |
| `garage_is_logged_in` | `true` / `false` |

---

## 13. Thanh Toán

| Phương thức | Chi tiết |
|---|---|
| Tiền mặt | Ghi nhận thủ công, nhập số tiền khách đưa |
| VietQR Techcombank | Tự sinh QR từ `img.vietqr.io` API, live update số tiền |
| Thẻ tín dụng | Ghi nhận thủ công |

**Tài khoản ngân hàng:**
- Chủ TK: DUONG CONG VINH
- STK: 4443338386
- Ngân hàng: Techcombank (TCB)

**Hotline:** 033.344.2358 (KT & đặt lịch) | 1900.6868 (Cứu hộ)

---

## 14. Bảo Mật

| Biện pháp | Chi tiết |
|---|---|
| JWT Auth | Mọi admin endpoint yêu cầu Bearer token |
| Route guard | `checkAuthPermission()` chặn admin.html khi chưa login |
| RBAC | UI ẩn/hiện theo role + backend validate |
| CORS | Origins whitelist trong main.py |
| Timeout | API: 10s, AI: 45s |
| Pydantic validation | Backend validate tất cả input |
| Anti-spam | Throttle yêu cầu đặt lịch cùng số 60s |

---

## 15. Deployment

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend: mở admin.html, customer.html trong browser
# Không cần build step — vanilla HTML/CSS/JS
```

### Docker
```bash
docker-compose up -d
# Backend: http://localhost:8000
```

### Railway (Production)
```bash
# Cấu hình railway.toml
railway up
```

### Vercel (Serverless)
```bash
vercel deploy
# api/index.py = ASGI adapter
# Static files served từ root
```

---

## 16. Những Cải Tiến trong v2.0 (18/09/2026)

| # | Vấn đề cũ | Fix trong v2.0 |
|---|---|---|
| 1 | Duplicate `view-customer-requests` section | ✅ Xóa bản trùng |
| 2 | `view-appointments` trong nav nhưng thiếu HTML section | ✅ Thêm section với 4 KPI + filter |
| 3 | Dashboard chart chỉ là container rỗng | ✅ Tích hợp Chart.js 4.4.3 với gradient bar |
| 4 | KPI cards hardcode số, không animation | ✅ CSS countUp animation + skeleton loader |
| 5 | Sidebar thiếu visual hierarchy | ✅ Section labels, active indicator, footer user info |
| 6 | Inline styles quá dài, khó bảo trì | ✅ Trích xuất thành reusable CSS classes |
| 7 | Theme toggle không update chart colors | ✅ Hook `toggleTheme()` → update Chart.js scales |
| 8 | Script Chart.js thiếu trong HTML | ✅ Thêm CDN script tag |
| 9 | Sidebar không hiển thị thông tin user | ✅ Thêm sidebar footer với role display |
| 10 | Script fix tạm thời còn tồn tại | ✅ Đã xóa 6 file fix scripts |

---

## 17. Kế Hoạch Phát Triển Tiếp Theo

| Sprint | Tính năng | Ưu tiên |
|---|---|---|
| v2.1 | Báo cáo doanh thu nâng cao (theo tháng/quý/năm) | 🔴 Cao |
| v2.1 | Export PDF hóa đơn | 🔴 Cao |
| v2.2 | Notification browser (Web Push) | 🟡 Trung bình |
| v2.2 | Tích hợp SMS/Zalo OA | 🟡 Trung bình |
| v2.3 | Barcode scanner phụ tùng | 🟢 Thấp |
| v2.3 | PWA (Progressive Web App) | 🟢 Thấp |
| v3.0 | Multi-branch support | 🔴 Cao |
| v3.0 | Inventory analytics, cảnh báo hết hàng | 🟡 Trung bình |

---

*Báo cáo này được sinh tự động bởi AI Antigravity dựa trên phân tích toàn bộ codebase ngày 18/09/2026.*
