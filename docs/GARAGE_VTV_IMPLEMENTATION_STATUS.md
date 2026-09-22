# BẢNG TỔNG HỢP TRẠNG THÁI TRIỂN KHAI HỆ THỐNG
# GARAGE VTV ENGINE PRO — IMPLEMENTATION STATUS MATRIX

---

## 1. QUY TẮC PHÂN LOẠI TRẠNG THÁI (STATUS CLASSIFICATION RULES)

Mọi tính năng, mô-đun và thành phần kỹ thuật trong hệ thống **Garage VTV Engine Pro** được thẩm định và phân loại nghiêm ngặt vào một trong 4 nhóm sau:

1. **`IMPLEMENTED` (Đã triển khai hoàn chỉnh):**
   - Đã có mã nguồn thực tế ở Backend (FastAPI / SQLAlchemy) và Frontend (`index.html`, `admin.html`, `login.html`, `customer.html`, `app.js`).
   - Đã có kịch bản kiểm thử tự động (Unit Test / Integration Test) hoặc kiểm thử thủ công xác nhận hoạt động chính xác.
2. **`PARTIALLY IMPLEMENTED` (Đã triển khai một phần):**
   - Đã có khung mã nguồn hoặc logic xử lý một phần, giao diện đã hiển thị nhưng chưa hoàn thiện toàn bộ các luồng phụ hoặc xử lý đồng bộ nâng cao.
3. **`DOCUMENTED / NOT VERIFIED` (Có trong tài liệu nhưng chưa đủ bằng chứng xác nhận):**
   - Xuất hiện trong tài liệu thiết kế ban đầu hoặc báo cáo mô tả nhưng trong mã nguồn thực tế chưa có code kiểm chứng đầy đủ.
4. **`ROADMAP` (Định hướng phát triển tương lai):**
   - Nằm trong kế hoạch mở rộng các phiên bản tiếp theo (v2.1, v2.2, v2.3, v3.0). Tuyệt đối không được coi là đã hoàn thành.

---

## 2. BẢNG TRẠNG THÁI TRIỂN KHAI CHI TIẾT THEO PHÂN HỆ (DETAILED IMPLEMENTATION MATRIX)

| STT | Phân hệ (Module) | Thành phần chức năng | Trạng thái kỹ thuật | Bằng chứng mã nguồn / Kiểm thử | Ghi chú & Đánh giá |
|:---:|---|---|:---:|---|---|
| **1** | **Authentication** | Đăng nhập tài khoản, mã hóa mật khẩu Bcrypt, phát hành JWT Token | **`IMPLEMENTED`** | `backend/app/routers/auth.py`<br>`backend/app/core/security.py`<br>File test: `test_master_suite.py` (TC13) | Hỗ trợ đăng nhập form JWT Bearer chuẩn RFC 7519. |
| **2** | **Authorization (RBAC)** | Phân quyền vai trò: Manager, Receptionist, Technician, Cashier | **`IMPLEMENTED`** | `backend/app/routers/` (Dependencies `get_current_user`, `require_role`)<br>File test: TC05, TC06 | Chặn truy cập trái quyền ở cấp tầng API Backend (403 Forbidden). |
| **3** | **Object-Level Authorization** | Chống IDOR: KTV chỉ được cập nhật phiếu sửa chữa được giao | **`IMPLEMENTED`** | `verify_technician_access` trong `backend/app/routers/repair_orders.py`<br>File test: TC04 | Chặn triệt để lỗ hổng KTV sửa chẩn đoán hoặc trạng thái của phiếu KTV khác. |
| **4** | **Customer Management** | Quản lý khách hàng, sinh mã `CUS-YYYY-XXXXXX`, Soft-delete | **`IMPLEMENTED`** | `backend/app/routers/customers.py`<br>`backend/app/models.py` (`Customer`)<br>File test: TC01, TC14 | Xóa mềm bảo toàn toàn bộ lịch sử sửa chữa của xe thuộc khách hàng. |
| **5** | **Vehicle Management** | Quản lý hồ sơ xe, ràng buộc duy nhất biển số xe | **`IMPLEMENTED`** | `backend/app/routers/vehicles.py`<br>`backend/app/models.py` (`Vehicle`)<br>File test: TC02 | Biển số xe unique constraint ở tầng Database SQLite. |
| **6** | **Appointment** | Đặt lịch hẹn, phát hiện trùng lịch xe trong khung giờ | **`IMPLEMENTED`** | `backend/app/routers/appointments.py`<br>`backend/app/models.py` (`Appointment`)<br>File test: TC03 | Kiểm tra xung đột lịch hẹn trong cửa sổ $\pm 60$ phút. |
| **7** | **Customer Requests** | Tiếp nhận yêu cầu đặt lịch online từ Landing Page công khai | **`IMPLEMENTED`** | `backend/app/routers/customer_requests.py`<br>`customer.html`, `index.html` | Khách vãng lai gửi yêu cầu không cần tài khoản nội bộ. |
| **8** | **Vehicle Reception** | Tiếp nhận xe tại xưởng, ghi nhận Odometer, xăng, trầy xước | **`IMPLEMENTED`** | `backend/app/models.py` (`VehicleReception`)<br>`admin.html` (Tab Tiếp nhận xe) | Lưu tình trạng ngoại thất, đồ đạc trên xe trước khi vào xưởng. |
| **9** | **Repair Order (Core)** | Tạo và quản lý phiếu sửa chữa xe | **`IMPLEMENTED`** | `backend/app/routers/repair_orders.py`<br>`backend/app/models.py` (`RepairOrder`) | Quản lý thông tin triệu chứng, phân công KTV phụ trách. |
| **10** | **State Machine Workflow** | Kiểm soát vòng đời 13 trạng thái sửa chữa bằng máy trạng thái nghiêm ngặt | **`IMPLEMENTED`** | `backend/app/services/repair_order_service.py` (`ALLOWED_TRANSITIONS`)<br>File test: TC15, TC18 - TC29 | Chặn tuyệt đối nhảy cóc trạng thái (Illegal State Transition). |
| **11** | **Inspection / Diagnosis** | Chẩn đoán kỹ thuật phân loại hạng mục, ghi nhận độ nghiêm trọng | **`IMPLEMENTED`** | `backend/app/models.py` (`Inspection`)<br>`backend/app/routers/repair_orders.py` | Phân loại ENGINE, BRAKES, SUSPENSION,... mức độ NORMAL đến CRITICAL. |
| **12** | **Parts & Inventory** | Quản lý linh kiện, giá nhập, giá bán, tồn kho tối thiểu | **`IMPLEMENTED`** | `backend/app/routers/inventory.py`<br>`backend/app/models.py` (`Part`, `InventoryTransaction`) | Ghi nhận thẻ kho, lịch sử nhập/xuất/điều chỉnh tồn. |
| **13** | **No Negative Stock Rule** | Quy tắc kiểm soát kho: Không xuất âm kho phụ tùng | **`IMPLEMENTED`** | `backend/app/services/inventory_service.py`<br>File test: TC07 | Tự động rollback giao dịch nếu tồn kho thực tế nhỏ hơn nhu cầu xuất. |
| **14** | **Quotation Management** | Lập báo giá linh kiện & tiền công, kiểm soát thời hạn hiệu lực | **`IMPLEMENTED`** | `backend/app/services/quotation_service.py`<br>`backend/app/routers/quotations.py`<br>File test: TC16 | Báo giá hết hạn (`valid_until < now()`) bị chặn duyệt ở Backend. |
| **15** | **Server-Side Financials** | Thẩm quyền tính toán tài chính độc quyền tại máy chủ | **`IMPLEMENTED`** | `QuotationService.calculate_totals`<br>File test: TC09 | Client không được can thiệp Subtotal, Discount, VAT (10%), Total. |
| **16** | **Invoice Generation** | Lập hóa đơn thanh toán từ phiếu sửa chữa hoàn thành | **`IMPLEMENTED`** | `backend/app/routers/invoices.py`<br>`backend/app/models.py` (`Invoice`) | Hóa đơn liên kết 1-1 với RepairOrder; khóa sửa chữa khi xuất hóa đơn. |
| **17** | **Payment & No Overpayment** | Ghi nhận thanh toán hóa đơn, chặn thanh toán vượt dư nợ | **`IMPLEMENTED`** | `backend/app/services/payment_service.py`<br>`backend/app/models.py` (`Payment`)<br>File test: TC08, TC17 | Chặn thanh toán vượt `balance_due`; Chặn thanh toán hóa đơn CANCELLED. |
| **18** | **VietQR Napas Gateway** | Tạo mã QR chuyển khoản động chuẩn Napas 247 | **`IMPLEMENTED`** | `admin.html`, `app.js` (Hàm `generateVietQR`) | Tạo QR kèm ngân hàng, số tài khoản, số tiền và nội dung tự động. |
| **19** | **AI Assistant (Gemini)** | Trợ lý AI hỏi đáp, tóm tắt lịch sử, giải thích bệnh xe | **`IMPLEMENTED`** | `backend/app/routers/ai.py`<br>`backend/app/ai/providers/gemini.py`<br>File test: TC10, TC11 | Gọi Google Gemini API, làm sạch dữ liệu PII trước khi gửi. |
| **20** | **AI Resilience & Fallback** | Dự phòng thông minh khi AI mất mạng / hết quota | **`IMPLEMENTED`** | `backend/app/ai/providers/fallback.py`<br>File test: TC12 | Tự động fallback dựa trên bảng tri thức kỹ thuật nội bộ. |
| **21** | **Realtime Updates (SSE)** | Cập nhật dữ liệu thời gian thực qua Server-Sent Events | **`IMPLEMENTED`** | `backend/app/routers/realtime.py`<br>`app.js` (EventSource SSE) | Tự động đồng bộ màn hình Dashboard khi có phát sinh dữ liệu mới. |
| **22** | **Offline Fallback Engine** | Chế độ làm việc ngoại tuyến lưu trữ LocalStorage client | **`PARTIALLY IMPLEMENTED`** | `app.js` (`vtv_db_*` LocalStorage Engine) | Cho phép lưu tạm và tra cứu khi mất mạng; **chưa có cơ chế giải quyết xung đột (conflict resolution) 2 chiều**. |
| **23** | **Audit Logging** | Ghi vết nhật ký thao tác người dùng trên hệ thống | **`IMPLEMENTED`** | `backend/app/models.py` (`AuditLog`)<br>`backend/app/routers/audit_logs.py` | Ghi nhận `user_id`, `action`, `resource`, `ip_address`, `created_at`. |
| **24** | **Revenue Analytics** | Biểu đồ doanh thu ngày/tháng, phân bố dịch vụ (Chart.js) | **`IMPLEMENTED`** | `backend/app/routers/analytics.py`<br>`admin.html` (Chart.js) | Trực quan hóa doanh thu, số lượng đơn sửa chữa hoàn thành. |
| **25** | **Automated Data Backup** | Tự động sao lưu cơ sở dữ liệu định kỳ ra Drive/Cloud | **`DOCUMENTED / NOT VERIFIED`** | Tài liệu kiến trúc có đề cập | Chưa có cron job hoặc script sao lưu định kỳ tự động trong mã nguồn hiện tại. |
| **26** | **Xuất Hóa Đơn File PDF** | Xuất hóa đơn sửa chữa ra định dạng PDF chuẩn in ấn | **`ROADMAP (v2.1)`** | Định hướng phiên bản 2.1 | Hiện tại xuất hóa đơn qua lệnh in trình duyệt (`window.print()`). |
| **27** | **Web Push / SMS / Zalo OA** | Gửi tin nhắn tự động nhắc bảo dưỡng qua SMS hoặc Zalo | **`ROADMAP (v2.2)`** | Định hướng phiên bản 2.2 | Hiện tại hệ thống chưa tích hợp API Zalo OA hoặc SMS Brandname. |
| **28** | **Barcode / QR Scanner Kho** | Quét mã vạch linh kiện phụ tùng bằng camera thiết bị | **`ROADMAP (v2.3)`** | Định hướng phiên bản 2.3 | Hiện tại thủ kho nhập mã và tìm kiếm theo chuỗi ký tự trên giao diện. |
| **29** | **Multi-Branch (Đa cơ sở)** | Mở rộng quản lý chuỗi nhiều chi nhánh gara toàn quốc | **`ROADMAP (v3.0)`** | Định hướng phiên bản 3.0 | CSDL hiện tại thiết kế mô hình đơn cơ sở (Single Branch). |

---

## 3. TỔNG HỢP TỶ LỆ TRIỂN KHAI THEO TIÊU CHÍ KỸ THUẬT

| Trạng thái | Số lượng thành phần | Tỷ lệ phần trăm | Ghi chú đánh giá kỹ thuật |
|---|:---:|:---:|---|
| **IMPLEMENTED** | 22 | **75.9%** | Đầy đủ toàn bộ luồng cốt lõi từ Đặt lịch $\rightarrow$ Tiếp nhận $\rightarrow$ Sửa chữa $\rightarrow$ Kho $\rightarrow$ Thanh toán $\rightarrow$ AI $\rightarrow$ Audit. |
| **PARTIALLY IMPLEMENTED** | 1 | **3.4%** | Cơ chế Offline Client LocalStorage (cần bổ sung bộ giải quyết xung đột). |
| **DOCUMENTED / NOT VERIFIED** | 1 | **3.4%** | Tính năng sao lưu tự động định kỳ (Database Backup Job). |
| **ROADMAP** | 5 | **17.3%** | Các tính năng mở rộng lộ trình v2.1 – v3.0 (PDF, Zalo/SMS, Barcode, Multi-branch). |
| **TỔNG CỘNG** | **29** | **100.0%** | **Hệ thống đáp ứng xuất sắc các tiêu chuẩn vận hành thực tế.** |
