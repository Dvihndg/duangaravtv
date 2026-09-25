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
| **BR-01: Thẩm quyền tài chính Server** | UR-09: Số tiền công thợ và phụ tùng tính chính xác | **FR-15, FR-16** | **UC-07** (Lập hóa đơn) | Service `quotation_service.py`<br>`POST /api/v1/invoices` | **TC09** (Thẩm quyền tính tiền tại Server) | **PASS** |
| **BR-02: Không xuất âm kho phụ tùng** | UR-07: Xuất vật tư tự động đối trừ kho thực tế | **FR-11** | **UC-06** (Quản lý kho phụ tùng) | Service `inventory_service.py`<br>`POST /repair-orders/{id}/parts` | **TC07** (Chặn xuất âm kho linh kiện) | **PASS** |
| **BR-03: Không thanh toán vượt dư nợ** | UR-09: Thu đúng số tiền khách còn nợ | **FR-17** | **UC-07** (Ghi nhận thanh toán) | Service `payment_service.py`<br>`POST /invoices/{id}/payments` | **TC08** (Chặn thanh toán vượt dư nợ) | **PASS** |
| **BR-04: Hóa đơn hủy không nhận tiền** | UR-09: Hóa đơn hủy bị đóng băng giao dịch | **FR-17** | **UC-07** (Ghi nhận thanh toán) | Service `payment_service.py`<br>`POST /invoices/{id}/payments` | **TC17** (Hóa đơn hủy không nhận tiền) | **PASS** |
| **BR-05: Chuyển trạng thái nghiêm ngặt** | UR-06: Chuẩn hóa quy trình 13 bước tuần tự | **FR-14** | **UC-04** (Cập nhật tiến độ) | Service `repair_order_service.py`<br>`PATCH /repair-orders/{id}/status` | **TC15** (Chặn nhảy cóc trạng thái)<br>**TC18 - TC29** (Kiểm thử State Machine) | **PASS** |
| **BR-06: Phân quyền đối tượng KTV** | UR-05: KTV chỉ sửa phiếu được phân công | **FR-02, FR-08** | **UC-04** (Chẩn đoán sửa chữa) | Router `repair_orders.py`<br>`verify_technician_access` | **TC04** (Chống IDOR giữa KTV)<br>**TC05, TC06** (Kiểm tra RBAC) | **PASS** |
| **BR-07: Báo giá hết hạn không duyệt** | UR-08: Báo giá có thời hạn hiệu lực rõ ràng | **FR-12, FR-13** | **UC-04** (Phê duyệt báo giá) | Service `quotation_service.py`<br>`PATCH /quotations/{id}/approve` | **TC16** (Chặn duyệt báo giá hết hạn) | **PASS** |
| **BR-08: Ghi nhật ký kiểm toán** | UR-10: Lưu vết ai làm, vào lúc nào, IP nào | **FR-23** | **UC-08** (Nhật ký kiểm toán) | Router `audit_logs.py`<br>`GET /api/v1/audit-logs` | Tự động ghi nhận vào bảng `audit_logs` | **PASS** |
| **Xác thực phiên làm việc JWT** | UR-01: Đăng nhập và phân quyền theo vai trò | **FR-01, FR-02** | **UC-01** (Đăng nhập) | Router `auth.py`<br>`POST /api/v1/auth/login` | **TC13** (Chặn truy cập không token) | **PASS** |
| **Quản lý Khách hàng & Phương tiện** | UR-02: Tra cứu hồ sơ xe và chủ xe trong 3 giây | **FR-03, FR-04** | **UC-05** (Tra cứu lịch sử) | Routers `customers.py`, `vehicles.py`<br>`GET, POST /customers`, `/vehicles` | **TC01** (Tạo khách thành công)<br>**TC02** (Chặn biển số trùng) | **PASS** |
| **Đặt lịch trực tuyến công khai** | UR-03: Khách đặt lịch không cần đăng ký tài khoản | **FR-05, FR-06** | **UC-02** (Đặt lịch online) | Router `customer_requests.py`<br>`POST /customer-requests` | **TC03** (Kiểm tra xung đột lịch hẹn) | **PASS** |
| **Bảo toàn dữ liệu khi xóa khách** | UR-02: Xóa khách không mất hồ sơ lịch sử xe | **FR-03, FR-18** | **UC-05** (Tra cứu lịch sử) | Router `customers.py` (Cơ chế Soft-Delete) | **TC14** (Xóa mềm bảo toàn lịch sử) | **PASS** |
| **Trợ lý AI Hỗ trợ kỹ thuật** | UR-06: AI giải thích bệnh xe dễ hiểu | **FR-20** | **UC-04** (Trợ lý AI) | Router `ai.py` (Gemini & Fallback)<br>`POST /api/v1/ai/chat` | **TC10** (AI không sinh giá)<br>**TC11** (Xác thực JSON Schema)<br>**TC12** (Fallback khi mất mạng) | **PASS** |
| **Báo cáo Doanh thu & Thống kê** | UR-01: Biểu đồ doanh thu trực quan theo thời gian | **FR-19** | **UC-08** (Báo cáo doanh thu) | Router `analytics.py`<br>`GET /api/v1/analytics/revenue` | Kiểm thử tích hợp Chart.js API | **PASS** |
| **Đồng bộ thời gian thực SSE** | UR-06: Cập nhật dữ liệu tức thì không cần F5 | **FR-21** | Toàn bộ các Use Case | Router `realtime.py`<br>`GET /api/v1/realtime/events` | Kiểm thử kết nối EventSource | **PASS** |
