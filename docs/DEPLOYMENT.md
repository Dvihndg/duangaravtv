# HƯỚNG DẪN TRIỂN KHAI & VẬN HÀNH (DEPLOYMENT & OPERATIONAL GUIDE)
## HỆ THỐNG QUẢN LÝ GARAGE VTV TÍCH HỢP AI (GARAGE VTV AI MANAGEMENT SYSTEM)

---

## 1. MÔI TRƯỜNG VẬN HÀNH (ENVIRONMENTS)

### 1.1. Môi trường Cục bộ (Local Development)
- **Hệ điều hành**: Windows 11 / macOS / Linux (Ubuntu 22.04 LTS).
- **Ngôn ngữ & Runtime**: Python 3.10 - 3.12+.
- **Cơ sở dữ liệu**: SQLite (`garage.db`) hoặc PostgreSQL Local container.
- **Dịch vụ Trợ lý AI**: Google Gemini API, OpenAI API hoặc Offline Fallback Engine.

### 1.2. Môi trường Sản xuất Đám mây (Cloud Production)
- **Frontend & Serverless API**: Vercel Cloud Serverless (`duangaravtv.vercel.app`).
- **Cơ sở dữ liệu Sản xuất**: Supabase PostgreSQL với kết nối Pure-Python `pg8000` (không phụ thuộc `libpq.so.5` của hệ điều hành).
- **Cơ chế đệm khẩn cấp**: Tự động hạ cấp sang `/tmp/garage.db` (Zero Downtime) khi Supabase bảo trì.

---

## 2. TRIỂN KHAI BẰNG DOCKER & DOCKER COMPOSE

Dự án cung cấp tệp `docker-compose.yml` chuẩn mực gồm 3 dịch vụ liên kết chặt chẽ:
1. `backend`: Ứng dụng FastAPI Python chạy uvicorn tại cổng `8000`.
2. `postgres`: Hệ quản trị CSDL PostgreSQL 15 chính thức tại cổng `5432`.
3. `redis`: Bộ đệm cache và lưu trữ hàng đợi SSE / Rate Limiter tại cổng `6379`.

### Lệnh khởi chạy Docker:
```bash
# 1. Sao chép tệp biến môi trường
cp .env.example .env

# 2. Xây dựng và khởi chạy toàn bộ dịch vụ trong nền
docker compose up -d --build

# 3. Xem log hoạt động của các container
docker compose logs -f

# 4. Dừng toàn bộ hệ thống
docker compose down
```

---

## 3. CÁC BIẾN MÔI TRƯỜNG CHÍNH (`.env`)

| Tên biến | Giá trị mẫu | Ý nghĩa |
|---|---|---|
| `APP_ENV` | `production` / `development` | Môi trường ứng dụng |
| `DATABASE_URL` | `postgresql+pg8000://user:pass@host:5432/db` | Chuỗi kết nối CSDL |
| `SECRET_KEY` | `garage-vtv-prod-secret-key-32-chars-min` | Khóa bí mật ký JWT Token |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `1440` | Thời gian sống của Access Token (24h) |
| `AI_PROVIDER` | `gemini` / `openai` / `ollama` / `fallback` | Nhà cung cấp AI mặc định |
| `GEMINI_API_KEY` | `AIzaSy...` | Khóa API Google Gemini |
| `OPENAI_API_KEY` | `sk-...` | Khóa API OpenAI |
| `VAT_RATE` | `0.10` | Tỷ lệ thuế VAT mặc định (10%) |
| `DEFAULT_CURRENCY` | `VND` | Đơn vị tiền tệ chính |
| `CORS_ORIGINS` | `*` | Danh sách domain được phép gọi API |
