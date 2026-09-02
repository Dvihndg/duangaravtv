# CHIẾN LƯỢC & DANH MỤC KIỂM THỬ (TESTING SPECIFICATION)
## HỆ THỐNG QUẢN LÝ GARAGE VTV TÍCH HỢP AI (GARAGE VTV AI MANAGEMENT SYSTEM)

---

## 1. CHIẾN LƯỢC KIỂM THỬ (TESTING STRATEGY)
Hệ thống áp dụng mô hình Kim Tự Tháp Kiểm Thử (Testing Pyramid):
- **Unit Tests (Kiểm thử đơn vị)**: Kiểm tra các hàm tính toán tài chính (subtotal, VAT, discount, total balance), kiểm tra logic xác thực Pydantic schemas, các quy tắc chuyển đổi trạng thái State Machine.
- **Integration Tests (Kiểm thử tích hợp)**: Kiểm tra tương tác giữa API Routers, Business Services, và Cơ sở dữ liệu SQLite trong bộ nhớ (`sqlite:///:memory:`) với các transaction rollback độc lập.
- **End-to-End Tests (Kiểm thử luồng toàn diện)**: Kiểm tra quy trình nghiệp vụ đầy đủ từ Tạo khách hàng -> Xe -> Lịch hẹn -> Tiếp nhận -> Chẩn đoán -> Báo giá -> Duyệt -> Sửa chữa -> Hóa đơn -> Thanh toán -> Hoàn tất.

---

## 2. DANH MỤC 17 TEST CASES BẮT BUỘC (TC01 - TC17)

| Mã TC | Tên Ca Kiểm Thử | Mục Tiêu & Kỳ Vọng | Module |
|---|---|---|---|
| **TC01** | Tạo khách hàng thành công | Tạo mới khách hàng với đầy đủ thông tin hợp lệ, nhận mã CUS-YYYY-XXXXXX và HTTP 201 | Customer |
| **TC02** | Chặn biển số xe trùng lặp | Thêm xe mới với biển số đã tồn tại trong hệ thống phải nhận lỗi HTTP 400 | Vehicle |
| **TC03** | Phát hiện lịch hẹn trùng lặp | Đặt lịch hẹn cùng xe hoặc cùng khung giờ trùng lặp phải nhận cảnh báo xung đột | Appointment |
| **TC04** | KTV không thể sửa trái phép RO của người khác | Kỹ thuật viên A không được phép cập nhật RO được giao cho Kỹ thuật viên B (Phòng chống IDOR) | Repair Order |
| **TC05** | KTV không thể truy cập API thanh toán | Tài khoản với vai trò TECHNICIAN truy cập endpoint thanh toán phải nhận mã lỗi HTTP 403 Forbidden | RBAC |
| **TC06** | Thu ngân không được sửa phiếu chẩn đoán kỹ thuật | Tài khoản với vai trò CASHIER gửi chẩn đoán kỹ thuật xe phải nhận mã lỗi HTTP 403 | RBAC |
| **TC07** | Tồn kho không thể âm | Xuất linh kiện vượt quá số lượng tồn hiện có trong kho phải bị chặn và rollback giao dịch | Inventory |
| **TC08** | Thanh toán không vượt quá số dư còn lại | Số tiền thanh toán lớn hơn `balance_due` của hóa đơn phải bị từ chối với HTTP 400 | Payment |
| **TC09** | Tính toán tổng tiền thực hiện ở Server-side | Toàn bộ các phép tính `subtotal`, `vat` (10%), `total` do Backend tính, không tin số tiền Client gửi | Quotation / Invoice |
| **TC10** | AI không được tự sinh giá tiền tùy tiện | Kiểm tra phản hồi từ AI không được phép thay đổi đơn giá niêm yết trong cơ sở dữ liệu | AI Engine |
| **TC11** | Từ chối phản hồi JSON không đúng schema từ AI | Khi AI trả về JSON thiếu trường bắt buộc hoặc sai kiểu dữ liệu, hệ thống kích hoạt schema validation | AI Engine |
| **TC12** | Sự cố AI API không làm sập hệ thống | Khi ngắt kết nối mạng hoặc nhà cung cấp AI timeout, hệ thống tự kích hoạt Fallback Engine an toàn | AI Failure Handling |
| **TC13** | Người dùng chưa cấp quyền bị chặn vào Admin | Request không kèm JWT Token hoặc vai trò không hợp lệ khi truy cập admin API bị chặn HTTP 401/403 | Authentication |
| **TC14** | Xóa mềm khách hàng bảo toàn lịch sử sửa chữa | Khi thực hiện soft-delete khách hàng (`deleted_at`), các bản ghi lịch sử sửa chữa của xe vẫn nguyên vẹn | Soft Delete |
| **TC15** | Chuyển trạng thái RO không hợp lệ bị từ chối | Nhảy cóc trạng thái (ví dụ từ `RECEIVED` nhảy thẳng sang `COMPLETED`) bị từ chối HTTP 400 | State Machine |
| **TC16** | Báo giá hết hạn không được duyệt | Báo giá có `valid_until` trong quá khứ không được phép chuyển sang trạng thái `APPROVED` | Quotation |
| **TC17** | Hóa đơn đã hủy không nhận thanh toán | Cố tình ghi nhận thanh toán cho Hóa đơn ở trạng thái `CANCELLED` phải bị từ chối | Invoice & Payment |

---

## 3. LỆNH CHẠY KIỂM THỬ
Chạy toàn bộ bộ test bằng công cụ `pytest`:
```powershell
pytest backend/tests/ -v --tb=short
```
Để chạy riêng bộ kiểm thử các trường hợp kiểm thử bắt buộc:
```powershell
pytest backend/tests/test_master_suite.py -v
```
