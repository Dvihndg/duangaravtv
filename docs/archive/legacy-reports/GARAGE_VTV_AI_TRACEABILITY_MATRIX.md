# MA TRẬN TRUY VẾT YÊU CẦU TOÀN DIỆN (REQUIREMENTS TRACEABILITY MATRIX - RTM)
# HỆ THỐNG QUẢN LÝ GARAGE Ô TÔ TÍCH HỢP AI - GARAGE VTV ENGINE PRO

---

## 1. MỤC TIÊU CỦA MA TRẬN TRUY VẾT
Ma trận truy vết yêu cầu (Traceability Matrix) bảo đảm sự liền mạch và nhất quán tuyệt đối trong toàn bộ vòng đời phát triển phần mềm:
$$\text{Business Requirement (BR)} \longrightarrow \text{User Requirement (UR)} \longrightarrow \text{Functional Requirement (FR)} \longrightarrow \text{Use Case (UC)} \longrightarrow \text{Module / API} \longrightarrow \text{Test Case (TC)}$$
Mọi yêu cầu nghiệp vụ đều có mã nguồn xử lý tương ứng và được xác nhận bởi các kịch bản kiểm thử tự động độc lập.

---

## 2. BẢNG MA TRẬN TRUY VẾT CHI TIẾT

| Business Requirement (BR) | User Requirement (UR) | Functional Requirement (FR) | Use Case (UC) | Thành phần Module / API Backend | Kịch bản kiểm thử (Test Case) | Trạng thái nghiệm thu |
|---|---|---|---|---|---|:---:|
| **BR-01: Xác thực & Bảo mật phiên** | UR-01: Quản lý đăng nhập và phân quyền nhân sự theo vai trò | **FR-01, FR-02** | **UC-01** (Đăng nhập) | Module `auth.py`<br>`POST /api/v1/auth/login` | **TC13** (Chặn truy cập không token) | **PASS** |
| **BR-02: Quản lý Khách hàng & Phương tiện** | UR-02: Tra cứu hồ sơ xe và chủ xe trong 3 giây | **FR-03, FR-04** | **UC-05** (Tra cứu lịch sử) | Modules `customers.py`, `vehicles.py`<br>`GET, POST /api/v1/customers`<br>`GET, POST /api/v1/vehicles` | **TC01** (Tạo khách thành công)<br>**TC02** (Chặn biển số trùng) | **PASS** |
| **BR-03: Đặt lịch trực tuyến công khai** | UR-03: Khách đặt lịch không cần đăng ký tài khoản | **FR-05, FR-22** | **UC-02** (Đặt lịch online) | Module `customer_requests.py`<br>`POST /api/v1/customer-requests` | **TC03** (Kiểm tra xung đột lịch hẹn) | **PASS** |
| **BR-04: Tiếp nhận xe & Quản lý hiện trạng** | UR-04: Lễ tân ghi nhận Odometer, xăng, trầy xước | **FR-06, FR-07** | **UC-03** (Tiếp nhận xe) | Module `repair_orders.py`<br>`POST /api/v1/repair-orders` | **TC01, TC02** | **PASS** |
| **BR-05: Chẩn đoán & Phân công KTV** | UR-05: KTV nhận xe trên tablet, ghi nhận chẩn đoán | **FR-08** | **UC-04** (Lập phiếu sửa chữa) | Module `repair_orders.py`<br>`POST /repair-orders/{id}/diagnosis` | **TC04** (Chống IDOR giữa KTV)<br>**TC06** (Thu ngân không sửa chẩn đoán) | **PASS** |
| **BR-06: Máy trạng thái sửa chữa (State Machine)** | UR-06: Chuẩn hóa 13 bước, không bỏ sót khâu KCS | **FR-13, FR-14** | **UC-04** (Cập nhật tiến độ) | Service `repair_order_service.py`<br>`PATCH /repair-orders/{id}/status` | **TC15** (Chặn nhảy cóc trạng thái)<br>**TC18 - TC29** (Kiểm thử 12 bước State Machine) | **PASS** |
| **BR-07: Quản lý Kho & Chặn xuất âm kho** | UR-07: Xuất vật tư tự động đối trừ kho thực tế | **FR-09, FR-10** | **UC-06** (Quản lý kho phụ tùng) | Module `inventory.py`<br>`POST /api/v1/repair-orders/{id}/items` | **TC07** (Chặn xuất âm kho linh kiện) | **PASS** |
| **BR-08: Soạn thảo Báo giá & Kiểm soát hiệu lực** | UR-08: Khách nhận báo giá rõ ràng, có thời hạn | **FR-11, FR-12** | **UC-04** (Báo giá) | Module `quotations.py`<br>`POST /api/v1/quotations` | **TC16** (Chặn duyệt báo giá hết hạn) | **PASS** |
| **BR-09: Thẩm quyền tính toán tài chính tại Server** | UR-09: Số tiền công thợ và phụ tùng tính chính xác | **FR-15** | **UC-07** (Lập hóa đơn) | Service `financial_engine.py`<br>`POST /api/v1/invoices` | **TC09** (Thẩm quyền tính tiền tại Server) | **PASS** |
| **BR-10: Thanh toán hóa đơn & VietQR Napas** | UR-10: Thu tiền mặt hoặc quét mã QR ngân hàng | **FR-16** | **UC-07** (Ghi nhận thanh toán) | Module `payments.py`<br>`POST /invoices/{id}/payments` | **TC08** (Chặn thanh toán vượt dư nợ)<br>**TC17** (Hóa đơn hủy không nhận tiền) | **PASS** |
| **BR-11: Trợ lý AI Hỗ trợ kỹ thuật & Khách hàng** | UR-11: AI tóm tắt bệnh xe, giải thích ngôn ngữ dễ hiểu | **FR-19** | **UC-09** (Hỏi đáp Trợ lý AI) | Module `ai.py` (Gemini Provider)<br>`POST /api/v1/ai/chat` | **TC10** (AI không tự sinh giá)<br>**TC11** (Xác thực JSON Schema)<br>**TC12** (Fallback khi AI sập mạng) | **PASS** |
| **BR-12: Báo cáo Doanh thu & Thống kê kinh doanh** | UR-12: Biểu đồ doanh thu trực quan theo thời gian | **FR-18** | **UC-08** (Báo cáo doanh thu) | Module `analytics.py`<br>`GET /api/v1/analytics/revenue` | Kiểm thử tích hợp Chart.js API | **PASS** |
| **BR-13: Bảo toàn dữ liệu & Nhật ký kiểm toán** | UR-13: Không mất dữ liệu xe khi xóa khách, lưu log | **FR-21** | **UC-10** (Nhật ký kiểm toán) | Module `audit_logs.py`<br>`GET /api/v1/audit-logs` | **TC14** (Xóa mềm bảo toàn lịch sử) | **PASS** |
| **BR-14: Đồng bộ thời gian thực & Chế độ ngoại tuyến** | UR-14: Nhận thông báo tức thì, làm việc khi mất mạng | **FR-20** | Toàn bộ các Use Case | Module `realtime.py` (SSE Stream)<br>Client `app.js` (LocalStorage Engine) | Kiểm thử ngắt kết nối mạng | **PASS** |
