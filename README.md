# 🚘 HỆ THỐNG QUẢN LÝ GARAGE TÍCH HỢP AI (AI GARAGE MANAGEMENT SYSTEM)

Hệ thống Quản lý Garage Ô tô Tích hợp Trí tuệ Nhân tạo (AI Engine) hỗ trợ tự động hóa quy trình vận hành từ tiếp nhận xe, chẩn đoán, tóm tắt lịch sử sửa chữa, sinh báo giá nháp đến lập hóa đơn thanh toán và giải thích dịch vụ cho khách hàng bằng ngôn ngữ dễ hiểu.

---

## 🌟 TÍNH NĂNG NỔI BẬT

### 1. Quản lý Quy trình Garage Chuẩn hóa (RBAC 4 Vai trò)
- **Quản lý (Manager)**: Dashboard thống kê realtime doanh thu, dịch vụ phổ biến, phụ tùng tồn ít, quản lý giá catalog.
- **Lễ tân (Receptionist)**: Đặt lịch hẹn, tiếp nhận xe vào garage, tra cứu lịch sử sửa chữa theo biển số xe.
- **Kỹ thuật viên (Technician)**: Nhập ghi chú chẩn đoán kỹ thuật, thêm bớt công sửa chữa và phụ tùng thay thế.
- **Thu ngân (Cashier)**: Lập hóa đơn (tự tính thuế VAT 8%, chiết khấu), ghi nhận thanh toán tiền mặt / chuyển khoản.

### 2. Trí Tuệ Nhân Tạo (AI Engine Integration)
- 📌 **AI Tóm tắt lịch sử sửa chữa xe**: Phân tích các lần sửa chữa trước đây và tự động đưa ra cảnh báo các chi tiết hao mòn cho KTV khi tiếp nhận xe.
- 🗣️ **AI Giải thích dịch vụ dễ hiểu cho khách hàng**: Tự động chuyển đổi thông tin chẩn đoán máy móc phức tạp thành ngôn ngữ bình dân, dễ hiểu cho khách (Sử dụng đúng Prompt System theo bài toán).
- 📋 **AI Sinh báo giá nháp tự động**: Tính toán chi phí vật tư, tiền công, VAT và trình bày bảng báo giá nháp lịch sự cho khách duyệt.
- ⚡ **Lớp AI Fallback thông minh**: Đảm bảo hệ thống vận hành 100% không bị ngắt quãng ngay cả khi không có Internet hoặc chưa nhập API Key.

---

## 🛠️ HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY

### 1. Yêu cầu hệ thống
- Python 3.10 trở lên
- Trình duyệt web hiện đại (Chrome, Edge, Firefox, Safari)

### 2. Cài đặt môi trường
Mở terminal PowerShell/CMD tại thư mục dự án và chạy các lệnh sau:

```powershell
# 1. Cài đặt các thư viện Python phụ thuộc
pip install -r requirements.txt

# 2. Khởi tạo file môi trường .env (Nếu chưa có)
cp .env.example .env
```

> **Ghi chú về AI API Key**: Bạn có thể điền `GEMINI_API_KEY` trong file `.env` để sử dụng Google Gemini LLM thực tế. Nếu để trống, hệ thống sẽ sử dụng **Smart AI Fallback Engine** tích hợp sẵn mà vẫn đảm bảo đầy đủ kết quả theo đúng yêu cầu!

### 3. Nạp dữ liệu mẫu (Seed Data)
Chạy script nạp dữ liệu mẫu bao gồm tài khoản 4 vai trò, xe ô tô, dịch vụ, phụ tùng và phiếu sửa chữa:

```powershell
python seed_data.py
```

### 4. Chạy Kiểm Thử Tự Động (Run Tests)
Chạy bộ test suite `pytest` kiểm thử tính năng Lịch hẹn, Phiếu sửa chữa, Hóa đơn và các tính năng AI:

```powershell
pytest backend/tests/ -v
```

### 5. Khởi chạy Hệ thống Web Application
Chạy FastAPI backend server:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

Truy cập hệ thống trên trình duyệt:
- 🌐 **Giao diện Web Dashboard**: `http://127.0.0.1:8000`
- 📚 **Tài liệu API Swagger**: `http://127.0.0.1:8000/docs`

---

## 🔑 TÀI KHOẢN ĐĂNG NHẬP MẪU (Hoặc sử dụng Thanh chuyển đổi nhanh trên Web)

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| **Quản Lý (Manager)** | `admin` | `admin123` |
| **Lễ Tân (Receptionist)** | `letan` | `letan123` |
| **Kỹ Thuật Viên (Technician)** | `kythuat` | `tech123` |
| **Thu Ngân (Cashier)** | `thungan` | `cashier123` |

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
demotesthethong/
├── backend/
│   ├── app/
│   │   ├── ai/               # AI Engine, Prompts & Fallback Service
│   │   ├── routers/          # API Routers (Auth, Customers, Orders, Invoices, AI)
│   │   ├── auth.py           # JWT Security & RBAC
│   │   ├── config.py         # Config reader (.env)
│   │   ├── database.py       # SQLAlchemy Session
│   │   ├── main.py           # FastAPI entrypoint
│   │   ├── models.py         # CSDL Models (3NF)
│   │   └── schemas.py        # Pydantic Schemas
│   └── tests/                # Test Suite (pytest)
├── frontend/
│   ├── index.html            # Web Dashboard SPA
│   ├── styles.css            # Glassmorphism Design System
│   └── app.js                # State Management & API Integration
├── docs/
│   └── SDLC_REPORT.md        # Báo cáo Kỹ thuật 4 giai đoạn SDLC (KT1-KT4)
├── seed_data.py              # Script nạp dữ liệu mẫu
├── requirements.txt          # Thư viện phụ thuộc
├── .env.example              # Mẫu cấu hình môi trường
└── README.md                 # Hướng dẫn sử dụng
```
