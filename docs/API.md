# TÀI LIỆU ĐẶC TẢ REST API (API DOCUMENTATION)
## HỆ THỐNG QUẢN LÝ GARAGE VTV TÍCH HỢP AI (GARAGE VTV AI MANAGEMENT SYSTEM)

---

## 1. QUY ƯỚC CHUNG (GENERAL CONVENTIONS)
- **Base URL**: `/api/v1` (hoặc `/api` theo chuẩn hệ thống).
- **Format dữ liệu**: JSON (`Content-Type: application/json; charset=utf-8`).
- **Xác thực (Authentication)**: Bearer Token JWT truyền qua header `Authorization: Bearer <access_token>`.
- **Cấu trúc phản hồi chuẩn hóa (Standard Response Structure)**:
  - Khi thành công (`200 OK`, `201 Created`):
    ```json
    {
      "success": true,
      "data": { ... },
      "message": "Thao tác thành công"
    }
    ```
  - Khi có lỗi (`400`, `401`, `403`, `404`, `422`, `500`):
    ```json
    {
      "success": false,
      "error_code": "INVALID_STATE_TRANSITION",
      "message": "Không thể chuyển trạng thái phiếu sửa chữa từ RECEIVED sang COMPLETED.",
      "details": {}
    }
    ```

---

## 2. DANH SÁCH CÁC NHÓM API CHÍNH

### 2.1. Authentication (`/api/v1/auth`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Công khai | Đăng nhập hệ thống (OAuth2 Password flow), nhận access_token |
| `POST` | `/api/v1/auth/refresh` | Công khai | Làm mới Access Token bằng Refresh Token |
| `POST` | `/api/v1/auth/logout` | Authenticated | Đăng xuất và thu hồi phiên làm việc |
| `GET` | `/api/v1/auth/me` | Authenticated | Xem thông tin tài khoản và quyền hạn hiện tại |

### 2.2. Khách Hàng (`/api/v1/customers`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/customers` | Tất cả vai trò | Lấy danh sách khách hàng (phân trang, tìm kiếm theo tên, SĐT) |
| `POST` | `/api/v1/customers` | Manager, Receptionist | Thêm mới hồ sơ khách hàng |
| `GET` | `/api/v1/customers/{id}` | Tất cả vai trò | Xem thông tin chi tiết khách hàng và danh sách xe sở hữu |
| `PUT` | `/api/v1/customers/{id}` | Manager, Receptionist | Cập nhật thông tin khách hàng |
| `DELETE` | `/api/v1/customers/{id}` | Manager | Xóa mềm khách hàng (bảo toàn lịch sử sửa chữa trong CSDL) |

### 2.3. Quản Lý Xe (`/api/v1/vehicles`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/vehicles` | Tất cả vai trò | Lấy danh sách phương tiện (tìm theo Biển số, số VIN) |
| `POST` | `/api/v1/vehicles` | Manager, Receptionist | Thêm xe mới vào hồ sơ khách hàng |
| `GET` | `/api/v1/vehicles/{id}` | Tất cả vai trò | Xem chi tiết thông số kỹ thuật xe |
| `PUT` | `/api/v1/vehicles/{id}` | Manager, Receptionist | Sửa thông tin xe, số km mới nhất |
| `GET` | `/api/v1/vehicles/{id}/history`| Tất cả vai trò | **Tra cứu toàn bộ lịch sử sửa chữa timeline của xe** |

### 2.4. Lịch Hẹn (`/api/v1/appointments`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/appointments` | Tất cả vai trò | Danh sách lịch hẹn theo ngày / tuần / tháng |
| `POST` | `/api/v1/appointments` | Manager, Receptionist | Đặt lịch hẹn mới (Tự động kiểm tra xung đột thời gian) |
| `GET` | `/api/v1/appointments/{id}` | Tất cả vai trò | Xem chi tiết lịch hẹn |
| `PUT` | `/api/v1/appointments/{id}` | Manager, Receptionist | Cập nhật ngày giờ, phân công nhân sự đón tiếp |
| `PATCH` | `/api/v1/appointments/{id}/status` | Manager, Receptionist | Chuyển trạng thái (`CONFIRMED`, `ARRIVED`, `CANCELLED`) |

### 2.5. Tiếp Nhận Xe (`/api/v1/receptions`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `POST` | `/api/v1/receptions` | Manager, Receptionist | Lập biên bản tiếp nhận xe (km, xăng, ảnh vết xước, yêu cầu) |
| `GET` | `/api/v1/receptions/{id}` | Tất cả vai trò | Xem biên bản tiếp nhận |

### 2.6. Phiếu Sửa Chữa (`/api/v1/repair-orders`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/repair-orders` | Tất cả vai trò | Lấy danh sách phiếu sửa chữa (lọc theo trạng thái State Machine) |
| `POST` | `/api/v1/repair-orders` | Manager, Receptionist | Tạo phiếu sửa chữa mới từ Biên bản tiếp nhận xe |
| `GET` | `/api/v1/repair-orders/{id}` | Tất cả vai trò | Xem toàn bộ thông tin RO, các hạng mục phụ tùng, công thợ, chẩn đoán |
| `PUT` | `/api/v1/repair-orders/{id}` | Manager, Receptionist | Sửa thông tin phiếu |
| `PATCH` | `/api/v1/repair-orders/{id}/status` | Manager, Receptionist, Tech | **Chuyển trạng thái State Machine (kiểm duyệt luồng nghiêm ngặt)** |
| `POST` | `/api/v1/repair-orders/{id}/inspection` | Manager, Technician | Ghi kết quả chẩn đoán kỹ thuật (Engine, Brakes, Battery...) |
| `POST` | `/api/v1/repair-orders/{id}/services` | Manager, Receptionist, Tech | Thêm dịch vụ kỹ thuật vào phiếu |
| `POST` | `/api/v1/repair-orders/{id}/parts` | Manager, Receptionist, Tech | Thêm phụ tùng vào phiếu (Kiểm tra tồn kho và ghi nhận xuất kho) |
| `POST` | `/api/v1/repair-orders/{id}/assign-technician` | Manager, Receptionist | Phân công Kỹ thuật viên phụ trách |

### 2.7. Báo Giá Dịch Vụ (`/api/v1/quotations`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/quotations` | Manager, Receptionist, Cashier | Danh sách báo giá |
| `POST` | `/api/v1/quotations` | Manager, Receptionist | Khởi tạo báo giá cho phiếu sửa chữa (Server tự tính Subtotal, VAT 10%, Total) |
| `GET` | `/api/v1/quotations/{id}` | Manager, Receptionist, Cashier | Chi tiết bảng báo giá nháp |
| `POST` | `/api/v1/quotations/{id}/approve` | Manager, Receptionist | **Ghi nhận Khách duyệt báo giá (Chuyển RO sang APPROVED)** |
| `POST` | `/api/v1/quotations/{id}/reject` | Manager, Receptionist | Ghi nhận Khách từ chối báo giá (Chuyển RO sang CANCELLED) |

### 2.8. Hóa Đơn & Thanh Toán (`/api/v1/invoices` & `/api/v1/payments`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/invoices` | Manager, Cashier | Danh sách hóa đơn dịch vụ |
| `POST` | `/api/v1/invoices` | Manager, Cashier | Tạo hóa đơn từ Phiếu sửa chữa đã hoàn thành |
| `GET` | `/api/v1/invoices/{id}` | Manager, Cashier | Chi tiết hóa đơn (tổng tiền, số tiền đã trả, dư nợ) |
| `POST` | `/api/v1/payments` | Manager, Cashier | **Ghi nhận thanh toán Atomic (kiểm tra `amount <= balance_due`)** |

### 2.9. Trí Tuệ Nhân Tạo (`/api/v1/ai`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `POST` | `/api/v1/ai/history-summary` | Manager, Receptionist, Tech | Tóm tắt lịch sử bảo dưỡng và cảnh báo hao mòn |
| `POST` | `/api/v1/ai/service-explanation` | Manager, Receptionist, Tech | Chuyển ngữ kỹ thuật phức tạp thành lời giải thích bình dân |
| `POST` | `/api/v1/ai/draft-quotation` | Manager, Receptionist | Soạn thảo văn phong báo giá nháp chuyên nghiệp |
| `GET` | `/api/v1/ai/logs` | Manager | Tra cứu nhật ký AI logs, độ trễ và số lượng token tiêu thụ |

### 2.10. Báo Cáo & Thống Kê (`/api/v1/reports`)
| Phương thức | Endpoint | Vai trò cho phép | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/reports/revenue` | Manager, Cashier | Báo cáo doanh thu theo ngày, tháng, năm, xuất file CSV |
| `GET` | `/api/v1/reports/services`| Manager, Receptionist | Thống kê dịch vụ phổ biến nhất tại xưởng |
| `GET` | `/api/v1/reports/parts` | Manager | Thống kê phụ tùng xuất kho nhiều nhất & cảnh báo sắp hết |
| `GET` | `/api/v1/reports/technicians` | Manager | Thống kê hiệu suất và khối lượng công việc của từng KTV |
