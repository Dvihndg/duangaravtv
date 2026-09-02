# BÁO CÁO ỨNG DỤNG AI TRONG VÒNG ĐỜI PHÁT TRIỂN PHẦN MỀM (SDLC AI USAGE REPORT)
## HỆ THỐNG QUẢN LÝ GARAGE VTV TÍCH HỢP AI (GARAGE VTV AI MANAGEMENT SYSTEM)

---

## 1. GIAI ĐOẠN 1: PHÂN TÍCH YÊU CẦU & THIẾT KẾ HỆ THỐNG (ANALYSIS & DESIGN)
Trong giai đoạn khởi tạo, AI được sử dụng làm chuyên gia kiến trúc phần mềm và kỹ sư quy trình nghiệp vụ:
- **Phân tích yêu cầu nghiệp vụ**: Chuẩn hóa quy trình dịch vụ ô tô từ tiếp nhận, chẩn đoán, báo giá đến xuất xưởng thành sơ đồ chuỗi (Sequence Diagram) và ma trận phân quyền (RBAC Matrix).
- **Thiết kế Cơ sở dữ liệu Chuẩn 3NF**: Hỗ trợ thiết kế sơ đồ thực thể liên kết (ERD) gồm 18 bảng với đầy đủ khóa chính, khóa ngoại, chỉ mục hiệu năng cao và ràng buộc toàn vẹn dữ liệu.
- **Hoạch định Lớp Trừu Tượng AI**: Thiết kế kiến trúc `AIProvider` độc lập để hệ thống không phụ thuộc vào bất kỳ một nhà cung cấp LLM cụ thể nào.

---

## 2. GIAI ĐOẠN 2: PHÁT TRIỂN & XÂY DỰNG MÃ NGUỒN (DEVELOPMENT & CODING)
Trong giai đoạn lập trình, AI hỗ trợ tối ưu hóa và sinh mã chuẩn công nghiệp:
- **Tạo Models & Pydantic Schemas v2**: Sinh các lớp thực thể SQLAlchemy 2.0 và schema xác thực dữ liệu chặt chẽ cho toàn bộ các thực thể nghiệp vụ.
- **Thiết kế Máy Trạng Thái (State Machine)**: Triển khai logic kiểm soát chuyển đổi trạng thái phi tuyến tính cho Phiếu Sửa Chữa (`RepairOrder`), ngăn chặn việc nhảy cóc trạng thái trái phép.
- **Bảo Mật Giao Dịch Tài Chính (Atomic Transactions)**: Áp dụng cơ chế khóa hàng và transaction rollback trong các nghiệp vụ trừ tồn kho và thanh toán hóa đơn để chống Race Condition và tồn kho âm.
- **Phát Triển Giao Diện Kép (Dual Interface)**: Xây dựng đồng thời giao diện Web SPA hiện đại và Streamlit Cyberpunk Dashboard phục vụ quản trị phân tích số liệu.

---

## 3. GIAI ĐOẠN 3: KIỂM THỬ TỰ ĐỘNG & BẢO MẬT (TESTING & SECURITY REVIEW)
Trong giai đoạn đảm bảo chất lượng, AI đóng vai trò Kỹ sư QA & Chuyên gia Bảo mật:
- **Thiết kế Bộ Test Case Tự Động (TC01 - TC17)**: Tự động tạo kịch bản kiểm thử bao phủ toàn bộ các trường hợp biên: biển số trùng lặp, xung đột lịch hẹn, kiểm tra phân quyền IDOR, tồn kho âm, và thanh toán vượt quá số dư.
- **Kiểm Thử Chống Tấn Công Prompt Injection**: Thử nghiệm các câu lệnh can thiệp độc hại vào ô chẩn đoán và xác nhận cơ chế thẻ `<UNTRUSTED_DATA>` cùng System Prompt phòng thủ hoạt động 100% tin cậy.
- **Rà Soát Lỗ Hổng Bảo Mật OWASP**: Kiểm tra bảo vệ chống SQL Injection, rò rỉ mã băm mật khẩu, phân quyền truy cập endpoint và cấu hình CORS.

---

## 4. GIAI ĐOẠN 4: ĐÓNG GÓI, VẬN HÀNH & TÀI LIỆU HÓA (DEPLOYMENT & FINALIZATION)
Trong giai đoạn xuất xưởng:
- **Tài Liệu Hóa Toàn Diện**: Biên soạn đầy đủ 10 tài liệu kỹ thuật chi tiết trong thư mục `docs/`.
- **Cấu Hình Container Hóa (Docker & Compose)**: Thiết lập môi trường Docker Compose gồm FastAPI Backend, PostgreSQL 15, và Redis sẵn sàng đưa vào vận hành thực tế.
- **Tối Ưu Hóa Serverless Trên Vercel**: Xây dựng cơ chế dự phòng kết nối thông minh với driver Pure Python `pg8000` và đệm SQLite `/tmp/garage.db` bảo đảm hệ thống vận hành 24/7 không gián đoạn (Zero Downtime).
