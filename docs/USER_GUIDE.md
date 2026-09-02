# SỔ TAY HƯỚNG DẪN SỬ DỤNG (USER GUIDE)
## HỆ THỐNG QUẢN LÝ GARAGE VTV TÍCH HỢP AI (GARAGE VTV AI MANAGEMENT SYSTEM)

---

## 1. HƯỚNG DẪN DÀNH CHO KHÁCH HÀNG (CUSTOMER PORTAL)
- **Truy cập**: [https://duangaravtv.vercel.app/](https://duangaravtv.vercel.app/)
- **Đặc quyền**: Không cần đăng nhập hoặc đăng ký tài khoản.
- **Các tính năng chính**:
  1. **Xem Bảng Giá & Danh Mục Dịch Vụ**: Tra cứu chi phí công thợ, các gói bảo dưỡng định kỳ và linh kiện phụ tùng có sẵn.
  2. **Gửi Yêu Cầu Đặt Lịch Hẹn Trực Tuyến**:
     - Điền Họ tên, Số điện thoại, Biển số xe, Hãng/dòng xe, Dịch vụ yêu cầu, Ngày giờ hẹn và Triệu chứng ban đầu.
     - Sau khi gửi thành công, hệ thống cấp ngay **Mã Tra Cứu Yêu Cầu** dạng `REQ-YYYYMMDD-XXXX`.
  3. **Tra Cứu Tiến Độ Sửa Chữa Trực Tuyến**:
     - Nhập Mã yêu cầu vào ô tìm kiếm để xem trực tiếp trạng thái xe (Đã tiếp nhận, Đang chẩn đoán, Đang sửa, Đã hoàn tất).
  4. **Tương tác với Trợ Lý AI Garage**:
     - Bấm biểu tượng cây đũa phép thần kỳ ở góc dưới màn hình để hỏi đáp kỹ thuật xe và nhận khuyến nghị tự động.

---

## 2. HƯỚNG DẪN DÀNH CHO LỄ TÂN (RECEPTIONIST)
- **Đăng nhập mẫu**: `letan` / `letan123`
- **Quy trình thao tác**:
  1. **Tiếp Nhận Khách Hàng**:
     - Vào menu **Lịch Hẹn / Yêu Cầu Dịch Vụ**, kiểm tra các yêu cầu khách gửi tới.
     - Bấm **Tiếp Nhận Xe** (Vehicle Reception): Nhập số km lúc vào xưởng, mức xăng hiện tại, chụp/đánh dấu các vết trầy xước bên ngoài và đồ vật quý trong xe.
  2. **Tạo Phiếu Sửa Chữa (RO)**:
     - Hệ thống sinh mã `RO-YYYY-XXXXXX`. Lễ tân chọn phân công Kỹ thuật viên phụ trách.
  3. **Lập Báo Giá Nháp Cho Khách Duyệt**:
     - Sau khi KTV kiểm tra xong, bấm **Tạo Báo Giá Nháp**: Hệ thống tự động tổng hợp tiền công và phụ tùng, cộng 10% VAT.
     - Sử dụng tính năng AI: Bấm **Giải thích dịch vụ** để AI tạo lời giải thích dễ hiểu gửi cho khách qua Zalo/SMS.
     - Khi khách đồng ý: Bấm **Phê duyệt báo giá (Approve)** để cho phép KTV bắt đầu sửa chữa.

---

## 3. HƯỚNG DẪN DÀNH CHO KỸ THUẬT VIÊN (TECHNICIAN)
- **Đăng nhập mẫu**: `kythuat` / `tech123`
- **Quy trình thao tác**:
  1. **Xem Xe Được Phân Công**: Vào mục **Phiếu Sửa Chữa**, lọc các phiếu có tên mình phụ trách.
  2. **Thực Hiện Khảo Sát Kỹ Thuật (Inspection)**:
     - Chọn từng hạng mục: Động cơ, Phanh, Hệ thống điện, Khung gầm, Lốp xe...
     - Đánh giá mức độ cảnh báo: Bình thường (Normal), Cần lưu ý (Notice), Cảnh báo (Warning), Nguy hiểm (Critical).
  3. **Đề Xuất Phụ Tùng & Dịch Vụ**:
     - Thêm các hạng mục cần thay thế (VD: Má phanh trước, Dầu máy 5W-30). Hệ thống sẽ tự động kiểm tra số lượng tồn kho khả dụng.
  4. **Cập Nhật Tiến Độ Sửa Chữa**:
     - Chuyển trạng thái phiếu sang `IN_REPAIR` khi bắt đầu làm, `WAITING_PARTS` nếu chờ linh kiện, và `QUALITY_CHECK` khi sửa xong.

---

## 4. HƯỚNG DẪN DÀNH CHO THU NGÂN (CASHIER)
- **Đăng nhập mẫu**: `thungan` / `cashier123`
- **Quy trình thao tác**:
  1. **Lập Hóa Đơn (Invoice)**:
     - Khi xe đã kiểm định chất lượng xong (`QUALITY_CHECK`), thu ngân vào mục Hóa Đơn và chọn **Lập Hóa Đơn**: Hệ thống chốt số tiền theo đúng báo giá đã được duyệt.
  2. **Thu Tiền & Ghi Nhận Thanh Toán (Payment)**:
     - Bấm **Thu Tiền**: Chọn hình thức (Tiền mặt, Chuyển khoản VietQR, Thẻ tín dụng).
     - Nhập số tiền thu (cho phép thanh toán từng phần hoặc thanh toán toàn bộ).
     - Khi số tiền đã thu bằng tổng hóa đơn (`balance_due = 0`), hóa đơn tự động chuyển trạng thái `PAID` và Phiếu sửa chữa chuyển sang `COMPLETED`.

---

## 5. HƯỚNG DẪN DÀNH CHO QUẢN LÝ (MANAGER / ADMIN)
- **Đăng nhập mẫu**: `admin` / `admin123`
- **Các tính năng nâng cao**:
  1. **Dashboard KPIs Realtime**: Theo dõi doanh thu theo ngày, tháng, số xe đang nằm xưởng, công suất làm việc của thợ.
  2. **Quản Lý Kho & Đơn Giá**: Cập nhật giá bán, giá nhập, định mức cảnh báo tồn ít cho từng mã phụ tùng.
  3. **Tra Cứu Nhật Ký Kiểm Toán (Audit Logs)**: Xem lịch sử thao tác của từng nhân viên, chống thất thoát gian lận.
  4. **Kiểm Soát AI Engine**: Tra cứu chi phí, số token tiêu thụ và độ chính xác của các lần gọi trợ lý ảo.
