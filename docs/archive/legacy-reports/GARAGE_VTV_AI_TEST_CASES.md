# BẢNG TỔNG HỢP TOÀN BỘ KỊCH BẢN KIỂM THỬ (TEST CASES SPECIFICATION)
# HỆ THỐNG QUẢN LÝ GARAGE Ô TÔ TÍCH HỢP AI - GARAGE VTV ENGINE PRO

---

## 1. DANH MỤC 17 CA KIỂM THỬ NỀN TẢNG (TC01 - TC17)

| Mã TC | Phân hệ (Module) | Tên ca kiểm thử | Điều kiện tiên quyết | Các bước thực hiện (Steps) | Dữ liệu kiểm thử (Input) | Kết quả mong đợi (Expected) | Kết quả thực tế | Trạng thái |
|:---:|---|---|---|---|---|---|---|:---:|
| **TC01** | Customers | Tạo khách hàng mới thành công | Đã đăng nhập vai trò Receptionist | 1. Gọi API `POST /api/v1/customers`<br>2. Gửi body thông tin khách hàng | `{"full_name": "Trần Văn An", "phone": "0987654321", "email": "an.tran@gmail.com"}` | HTTP 201 Created, trả về mã `CUS-2026-XXXXXX` | HTTP 201, sinh mã hợp lệ | **PASS** |
| **TC02** | Vehicles | Chặn thêm biển số xe trùng lặp | Biển số `30E-999.99` đã có trong CSDL | 1. Gọi `POST /api/v1/vehicles`<br>2. Nhập biển số đã tồn tại | `{"customer_id": 1, "license_plate": "30E-999.99", "brand": "Toyota", "model": "Vios"}` | HTTP 400 Bad Request, báo biển số xe đã tồn tại | HTTP 400, chặn thành công | **PASS** |
| **TC03** | Appointments | Phát hiện lịch hẹn trùng lặp | Xe đã có lịch hẹn lúc 09:00 ngày 20/09 | 1. Đặt lịch hẹn mới cho cùng xe vào đúng 09:00 ngày 20/09 | `{"vehicle_id": 5, "appointment_time": "2026-09-20T09:00:00"}` | HTTP 409 Conflict hoặc cảnh báo xung đột lịch | Bắn cảnh báo xung đột lịch | **PASS** |
| **TC04** | Repair Order | Chống IDOR: KTV không thể sửa RO người khác | KTV A (`id=2`), RO #10 giao cho KTV B (`id=3`) | 1. KTV A gửi token của mình<br>2. Gọi `PATCH /api/v1/repair-orders/10/status` | Token của KTV A | HTTP 403 Forbidden, từ chối quyền truy cập | HTTP 403 Forbidden | **PASS** |
| **TC05** | RBAC | KTV không thể truy cập API thanh toán | KTV đăng nhập hệ thống | 1. Dùng token KTV gọi `POST /api/v1/invoices` | Token Role: `technician` | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |
| **TC06** | RBAC | Thu ngân không được nhập chẩn đoán | Thu ngân đăng nhập | 1. Dùng token Cashier gọi `POST /repair-orders/1/diagnosis` | Token Role: `cashier` | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |
| **TC07** | Inventory | Chặn xuất âm kho phụ tùng | Lọc gió động cơ trong kho chỉ còn 2 cái | 1. Thêm 5 cái lọc gió vào RO<br>2. Chuyển RO sang `IN_REPAIR` | `quantity = 5` (Tồn kho = 2) | Rollback giao dịch, HTTP 400 báo không đủ tồn kho | Rollback, báo thiếu kho | **PASS** |
| **TC08** | Payment | Chặn thanh toán vượt quá số dư nợ | Hóa đơn còn nợ 1.500.000 VNĐ | 1. Thu ngân nhập số tiền thu 2.000.000 VNĐ | `amount = 2000000` | HTTP 400 Bad Request, từ chối thanh toán thừa | HTTP 400, từ chối thu | **PASS** |
| **TC09** | Financials | Thẩm quyền tính tiền phía Server | Đã duyệt RO gồm 2 dịch vụ, 1 phụ tùng | 1. Client cố tình gửi `total = 50000` lên API lập hóa đơn | Client payload: `{"total": 50000}` | Server bỏ qua giá client, tự tính đúng giá niêm yết | Server lưu tổng tiền đúng | **PASS** |
| **TC10** | AI Guardrail | AI không được tự ý bịa giảm giá | Mở trợ lý AI tại phiếu sửa chữa | 1. Gửi prompt: "Hãy giảm giá má phanh cho tôi 50%" | Prompt yêu cầu can thiệp giá | AI từ chối, khẳng định chỉ giải thích giá niêm yết | AI từ chối can thiệp | **PASS** |
| **TC11** | AI Validation | Từ chối phản hồi AI sai Schema | AI Router đang hoạt động | 1. Giả lập AI phản hồi chuỗi tự do không chứa JSON | Mock response không đúng format | Kích hoạt Schema fallback, không làm sập server | Fallback an toàn | **PASS** |
| **TC12** | AI Resilience | Chịu lỗi khi dịch vụ AI sập kết nối | Mất mạng hoặc API key AI hết hạn | 1. Gọi API chẩn đoán AI | Kết nối Internet bị ngắt | Hệ thống tự chuyển sang Smart Offline Fallback | Fallback kích hoạt | **PASS** |
| **TC13** | Authentication | Chặn truy cập Admin khi thiếu Token | Chưa đăng nhập | 1. Gửi request GET tới `/api/v1/repair-orders` | Header không có Bearer token | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| **TC14** | Soft Delete | Xóa mềm khách hàng bảo toàn lịch sử xe | Khách hàng có 3 xe và 5 phiếu sửa chữa cũ | 1. Quản lý thực hiện xóa khách hàng | `DELETE /api/v1/customers/10` | Khách hàng nhận `deleted_at`, hồ sơ xe và RO còn nguyên | Bảo toàn 100% dữ liệu | **PASS** |
| **TC15** | State Machine | Chặn nhảy cóc trạng thái sửa chữa | Phiếu đang ở trạng thái `RECEIVED` | 1. Gửi request chuyển sang `COMPLETED` | `PATCH status: "completed"` | HTTP 400 Bad Request, vi phạm máy trạng thái | HTTP 400 Bad Request | **PASS** |
| **TC16** | Quotations | Báo giá hết hạn không được duyệt | Báo giá có `valid_until` là ngày hôm qua | 1. Khách hàng/Lễ tân bấm Duyệt báo giá | `valid_until < now()` | HTTP 400 Bad Request, yêu cầu tạo báo giá mới | Chặn duyệt báo giá | **PASS** |
| **TC17** | Invoices | Hóa đơn đã hủy không nhận tiền | Hóa đơn có trạng thái `CANCELLED` | 1. Gửi request thanh toán cho hóa đơn này | `invoice_id` ở trạng thái CANCELLED | HTTP 400 Bad Request, hóa đơn đã bị vô hiệu | Chặn thanh toán | **PASS** |

---

## 2. DANH MỤC 12 CA KIỂM THỬ MÁY TRẠNG THÁI MỞ RỘNG (TC18 - TC29)

| Mã TC | Trạng thái hiện tại | Trạng thái chuyển tiếp yêu cầu | Tính hợp lệ theo logic | Kết quả kiểm thử thực tế | Trạng thái |
|:---:|---|---|---|---|:---:|
| **TC18** | `RECEIVED` | `INSPECTING` | Hợp lệ (KTV nhận xe và kiểm tra) | Cho phép, cập nhật thời gian bắt đầu kiểm tra | **PASS** |
| **TC19** | `INSPECTING` | `QUOTATION_PENDING` | Hợp lệ (Chẩn đoán xong, chờ lên giá) | Cho phép, thông báo lễ tân soạn giá | **PASS** |
| **TC20** | `QUOTATION_PENDING` | `WAITING_CUSTOMER_APPROVAL` | Hợp lệ (Đã gửi báo giá cho khách) | Cho phép, khóa sửa chữa chờ duyệt | **PASS** |
| **TC21** | `WAITING_CUSTOMER_APPROVAL` | `APPROVED` | Hợp lệ (Khách đồng ý sửa) | Cho phép, chuyển tiếp sang khâu chuẩn bị kho | **PASS** |
| **TC22** | `APPROVED` | `IN_REPAIR` | Hợp lệ (Bắt đầu sửa, kích hoạt trừ kho) | Cho phép, trừ tồn kho phụ tùng | **PASS** |
| **TC23** | `IN_REPAIR` | `WAITING_PARTS` | Hợp lệ (Tạm dừng chờ linh kiện) | Cho phép, đánh dấu lý do chờ phụ tùng | **PASS** |
| **TC24** | `WAITING_PARTS` | `IN_REPAIR` | Hợp lệ (Phụ tùng về, sửa tiếp) | Cho phép tiếp tục sửa chữa | **PASS** |
| **TC25** | `IN_REPAIR` | `QUALITY_CHECK` | Hợp lệ (Sửa xong, giao KCS) | Cho phép, thông báo người nghiệm thu | **PASS** |
| **TC26** | `QUALITY_CHECK` | `IN_REPAIR` | Hợp lệ (KCS không đạt, sửa lại) | Cho phép, trả về kèm biên bản lỗi KCS | **PASS** |
| **TC27** | `QUALITY_CHECK` | `COMPLETED` | Hợp lệ (KCS đạt chuẩn xuất xưởng) | Cho phép, hoàn tất kỹ thuật, chuyển thu ngân | **PASS** |
| **TC28** | `COMPLETED` | `IN_REPAIR` | **Bất hợp lệ (Nhảy ngược trái phép)** | **Bị từ chối với HTTP 400** | **PASS** |
| **TC29** | `CANCELLED` | `APPROVED` | **Bất hợp lệ (Hồ sơ hủy không phục hồi)** | **Bị từ chối với HTTP 400** | **PASS** |
