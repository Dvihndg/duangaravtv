# TÀI LIỆU THIẾT KẾ CƠ SỞ DỮ LIỆU TOÀN DIỆN (DATABASE DOCUMENTATION)
# HỆ THỐNG QUẢN LÝ GARAGE Ô TÔ TÍCH HỢP AI - GARAGE VTV ENGINE PRO

---

## 1. TỔNG QUAN CƠ SỞ DỮ LIỆU
- **Hệ quản trị CSDL:** SQLite 3 (`garage.db`)
- **Tầng ORM:** SQLAlchemy 2.x ORM
- **Chuẩn hóa thiết kế:** Bậc 3 (Third Normal Form - 3NF)
- **Tổng số bảng thực tế:** 21 bảng
- **Cơ chế toàn vẹn:** Khóa chính (PK), Khóa ngoại (FK), Ràng buộc duy nhất (Unique), Chỉ mục tìm kiếm (Index), Quản lý giao dịch nguyên tử (ACID Transactions).

---

## 2. DANH MỤC 21 BẢNG TRONG CƠ SỞ DỮ LIỆU THỰC TẾ

| STT | Tên bảng CSDL (`Table Name`) | Mục đích nghiệp vụ & Nội dung lưu trữ |
|:---:|---|---|
| **1** | `users` | Lưu trữ tài khoản nhân sự nội bộ, mật khẩu băm Bcrypt và vai trò (Role). |
| **2** | `customers` | Lưu trữ thông tin khách hàng, số điện thoại, địa chỉ và trạng thái xóa mềm. |
| **3** | `vehicles` | Lưu trữ hồ sơ phương tiện, biển số xe (Unique), số VIN, hãng xe, số km hiện tại. |
| **4** | `appointments` | Lưu trữ lịch hẹn bảo dưỡng/sửa chữa của xe theo khung thời gian. |
| **5** | `vehicle_receptions` | Biên bản tiếp nhận xe tại quầy: ghi nhận Odometer, mức xăng, vết xước, đồ đạc. |
| **6** | `services` | Danh mục các gói dịch vụ sửa chữa chuẩn, thời gian định mức và tiền công thợ. |
| **7** | `parts` | Danh mục phụ tùng linh kiện kho, đơn vị tính, giá nhập, giá bán niêm yết, tồn kho. |
| **8** | `inventory_transactions` | Thẻ kho chi tiết: ghi vết toàn bộ các giao dịch nhập kho, xuất kho sửa chữa, điều chỉnh tồn. |
| **9** | `repair_orders` | Bảng trung tâm: Phiếu lệnh sửa chữa xe, mã định danh, KTV phụ trách, trạng thái vòng đời. |
| **10** | `inspections` | Biên bản chẩn đoán kỹ thuật chi tiết theo các cụm hạng mục cơ khí kèm độ nghiêm trọng. |
| **11** | `repair_order_services` | Bảng liên kết chi tiết các dịch vụ tiền công thợ gắn vào một phiếu sửa chữa cụ thể. |
| **12** | `repair_order_parts` | Bảng liên kết chi tiết các linh kiện phụ tùng xuất từ kho lắp ráp cho phiếu sửa chữa. |
| **13** | `repair_order_items` | Bảng mở rộng liên kết hợp nhất giữa dịch vụ và phụ tùng theo phiếu sửa chữa. |
| **14** | `quotations` | Bảng báo giá sửa chữa gửi khách hàng, tổng tiền, ngày hết hạn hiệu lực (`valid_until`). |
| **15** | `quotation_items` | Chi tiết các dòng hạng mục công việc và phụ tùng nằm trong một bản báo giá. |
| **16** | `invoices` | Hóa đơn quyết toán thanh toán: Subtotal, Chiết khấu, Thuế VAT 10%, Tổng tiền, Dư nợ. |
| **17** | `payments` | Giao dịch thu tiền cho hóa đơn: số tiền, phương thức (Tiền mặt / Chuyển khoản VietQR). |
| **18** | `audit_logs` | Nhật ký kiểm toán: ghi nhận định danh người dùng, địa chỉ IP, hành động và thời gian. |
| **19** | `settings` | Bảng cấu hình tham số hệ thống: thông tin gara, tỷ lệ thuế VAT mặc định, hotline. |
| **20** | `ai_logs` | Nhật ký tương tác Trí tuệ Nhân tạo: lưu vết prompt, phản hồi, độ trễ ms, kiểm định an toàn. |
| **21** | `customer_requests` | Hàng đợi tiếp nhận yêu cầu đặt lịch hẹn trực tuyến từ Cổng thông tin khách hàng công khai. |

---

## 3. TỪ ĐIỂN DỮ LIỆU CHI TIẾT CÁC BẢNG CỐT LÕI (DATA DICTIONARY)

### 3.1. Bảng `users` (Nhân sự)
| Tên cột | Kiểu dữ liệu | PK | FK | Null | Unique | Mô tả chi tiết |
|---|---|:---:|:---:|:---:|:---:|---|
| `id` | INTEGER | ✔ | | | ✔ | Khóa chính tự tăng |
| `username` | VARCHAR(50) | | | | ✔ | Tên đăng nhập hệ thống |
| `email` | VARCHAR(100) | | | | ✔ | Địa chỉ email nhân sự |
| `hashed_password` | VARCHAR(255) | | | | | Mật khẩu băm một chiều Bcrypt |
| `full_name` | VARCHAR(100) | | | | | Họ và tên đầy đủ |
| `role` | VARCHAR(20) | | | | | Vai trò: `manager`, `receptionist`, `technician`, `cashier` |
| `phone` | VARCHAR(20) | | | ✔ | | Số điện thoại |
| `is_active` | BOOLEAN | | | | | Trạng thái kích hoạt (Default: True) |
| `created_at` | DATETIME | | | | | Thời gian tạo tài khoản |

### 3.2. Bảng `customers` (Khách hàng)
| Tên cột | Kiểu dữ liệu | PK | FK | Null | Unique | Mô tả chi tiết |
|---|---|:---:|:---:|:---:|:---:|---|
| `id` | INTEGER | ✔ | | | ✔ | Khóa chính tự tăng |
| `customer_code` | VARCHAR(30) | | | ✔ | ✔ | Mã khách: `CUS-YYYY-XXXXXX` |
| `full_name` | VARCHAR(100) | | | | | Họ và tên chủ xe |
| `phone` | VARCHAR(20) | | | | ✔ | Số điện thoại duy nhất |
| `email` | VARCHAR(100) | | | ✔ | | Địa chỉ email |
| `address` | VARCHAR(255) | | | ✔ | | Địa chỉ cư trú |
| `status` | VARCHAR(20) | | | | | Trạng thái: `ACTIVE`, `INACTIVE` |
| `deleted_at` | DATETIME | | | ✔ | | Timestamp xóa mềm (Soft-delete) |
| `created_at` | DATETIME | | | | | Thời gian tạo hồ sơ |

### 3.3. Bảng `vehicles` (Phương tiện)
| Tên cột | Kiểu dữ liệu | PK | FK | Null | Unique | Mô tả chi tiết |
|---|---|:---:|:---:|:---:|:---:|---|
| `id` | INTEGER | ✔ | | | ✔ | Khóa chính tự tăng |
| `license_plate` | VARCHAR(20) | | | | ✔ | Biển số xe duy nhất toàn hệ thống |
| `brand` | VARCHAR(50) | | | | | Hãng xe (Toyota, Honda, Mazda,...) |
| `model` | VARCHAR(50) | | | | | Dòng xe (Camry, CR-V, CX-5,...) |
| `year` | INTEGER | | | ✔ | | Năm sản xuất |
| `color` | VARCHAR(30) | | | ✔ | | Màu sơn xe |
| `vin_number` | VARCHAR(50) | | | ✔ | | Số khung định danh VIN |
| `current_mileage`| INTEGER | | | | | Số km đồng hồ hiện tại |
| `customer_id` | INTEGER | | `customers.id` | | | Khóa ngoại chủ sở hữu |
| `created_at` | DATETIME | | | | | Thời gian tạo hồ sơ xe |

### 3.4. Bảng `repair_orders` (Phiếu sửa chữa cốt lõi)
| Tên cột | Kiểu dữ liệu | PK | FK | Null | Unique | Mô tả chi tiết |
|---|---|:---:|:---:|:---:|:---:|---|
| `id` | INTEGER | ✔ | | | ✔ | Khóa chính tự tăng |
| `code` | VARCHAR(30) | | | | ✔ | Mã phiếu: `RO-YYYY-XXXXXX` |
| `vehicle_id` | INTEGER | | `vehicles.id` | | | Khóa ngoại xe sửa chữa |
| `customer_id` | INTEGER | | `customers.id` | ✔ | | Khóa ngoại chủ xe |
| `technician_id` | INTEGER | | `users.id` | ✔ | | Khóa ngoại KTV phụ trách |
| `receptionist_id` | INTEGER | | `users.id` | ✔ | | Khóa ngoại Lễ tân lập phiếu |
| `mileage_in` | INTEGER | | | | | Số km lúc nhận xe vào xưởng |
| `customer_complaint`| TEXT | | | ✔ | | Khiếu nại / Triệu chứng ban đầu |
| `technical_diagnosis`| TEXT | | | ✔ | | Kết luận chẩn đoán của KTV |
| `status` | VARCHAR(30) | | | | | Trạng thái vòng đời (13 states) |
| `ai_history_summary`| TEXT | | | ✔ | | Tóm tắt lịch sử do AI sinh |
| `created_at` | DATETIME | | | | | Thời gian lập phiếu |
| `completed_at` | DATETIME | | | ✔ | | Thời gian hoàn tất xuất xưởng |

### 3.5. Bảng `invoices` (Hóa đơn quyết toán)
| Tên cột | Kiểu dữ liệu | PK | FK | Null | Unique | Mô tả chi tiết |
|---|---|:---:|:---:|:---:|:---:|---|
| `id` | INTEGER | ✔ | | | ✔ | Khóa chính tự tăng |
| `invoice_number` | VARCHAR(30) | | | | ✔ | Mã hóa đơn: `INV-YYYY-XXXXXX` |
| `repair_order_id` | INTEGER | | `repair_orders.id`| | ✔ | Khóa ngoại 1-1 với phiếu sửa chữa |
| `subtotal` | FLOAT | | | | | Tổng tiền trước thuế |
| `discount_amount` | FLOAT | | | | | Số tiền chiết khấu giảm giá |
| `vat` | FLOAT | | | | | Tiền thuế VAT 10% do Server tính |
| `total_amount` | FLOAT | | | | | Tổng số tiền phải thanh toán |
| `paid_amount` | FLOAT | | | | | Số tiền lũy kế đã thanh toán |
| `balance_due` | FLOAT | | | | | Số dư nợ còn lại cần thu |
| `status` | VARCHAR(20) | | | | | Trạng thái: `UNPAID`, `PARTIAL`, `PAID`, `CANCELLED` |
| `created_at` | DATETIME | | | | | Thời gian phát hành hóa đơn |

### 3.6. Bảng `parts` (Linh kiện & Phụ tùng kho)
| Tên cột | Kiểu dữ liệu | PK | FK | Null | Unique | Mô tả chi tiết |
|---|---|:---:|:---:|:---:|:---:|---|
| `id` | INTEGER | ✔ | | | ✔ | Khóa chính tự tăng |
| `code` | VARCHAR(30) | | | | ✔ | Mã phụ tùng: `PAR-XXX` |
| `name` | VARCHAR(150) | | | | | Tên phụ tùng linh kiện |
| `category` | VARCHAR(50) | | | | | Nhóm linh kiện |
| `unit` | VARCHAR(20) | | | | | Đơn vị tính: Cái, Lít, Bình,... |
| `cost_price` | FLOAT | | | | | Đơn giá vốn nhập kho |
| `unit_price` | FLOAT | | | | | Đơn giá bán niêm yết |
| `stock_quantity` | INTEGER | | | | | Số lượng tồn kho khả dụng |
| `min_stock_alert`| INTEGER | | | | | Ngưỡng cảnh báo tồn kho tối thiểu |
| `is_active` | BOOLEAN | | | | | Trạng thái kinh doanh |

---

## 4. QUY TẮC RÀNG BUỘC TOÀN VẸN (DATA INTEGRITY RULES)
1. **Ràng buộc khóa ngoại:** Mọi liên kết từ `vehicles`, `repair_orders`, `invoices` đến `customers` đều bảo đảm không bị mồ côi.
2. **Cơ chế Soft-Delete:** Bảng `customers` sử dụng trường `deleted_at`. Khi quản lý xóa khách hàng, hệ thống chỉ cập nhật timestamp và chuyển trạng thái `INACTIVE`, không bao giờ xóa cứng dòng dữ liệu để bảo toàn 100% hồ sơ xe và lịch sử sửa chữa cũ.
3. **Chặn xuất âm kho:** Giao dịch xuất kho phụ tùng bắt buộc thỏa mãn `stock_quantity >= quantity`. Nếu không thỏa mãn, CSDL tự động ROLLBACK giao dịch.
