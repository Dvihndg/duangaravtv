# BỘ TÀI LIỆU SƠ ĐỒ UML TOÀN DIỆN (UML DIAGRAMS SPECIFICATION)
# HỆ THỐNG QUẢN LÝ GARAGE Ô TÔ TÍCH HỢP AI - GARAGE VTV ENGINE PRO

---

## 1. BIỂU ĐỒ USE CASE (USE CASE DIAGRAMS)

### 1.1. Biểu đồ Use Case Tổng Quát
```mermaid
graph TD
    Customer((Khách Hàng))
    Receptionist((Lễ Tân))
    Technician((Kỹ Thuật Viên))
    Cashier((Thu Ngân))
    Manager((Quản Lý / Admin))
    AI_Service[Google Gemini AI]

    subgraph "Hệ Thống Garage VTV Engine Pro"
        UC_Auth[UC-01: Đăng nhập & Quản lý phiên JWT]
        UC_Booking[UC-02: Đặt lịch hẹn sửa chữa online]
        UC_Reception[UC-03: Tiếp nhận xe & Ghi nhận Odometer]
        UC_RO[UC-04: Quản lý Phiếu sửa chữa State Machine]
        UC_History[UC-05: Tra cứu lịch sử sửa chữa]
        UC_Inventory[UC-06: Quản lý Kho linh kiện & Dịch vụ]
        UC_Billing[UC-07: Báo giá, Hóa đơn & VietQR]
        UC_Report[UC-08: Báo cáo Doanh thu Line Chart]
        UC_AI[UC-09: Trợ lý AI Tóm tắt & Giải thích]
        UC_Audit[UC-10: Nhật ký kiểm toán Audit Log]
    end

    Customer --> UC_Booking
    Customer --> UC_History
    Customer --> UC_AI

    Receptionist --> UC_Auth
    Receptionist --> UC_Reception
    Receptionist --> UC_Booking
    Receptionist --> UC_Billing
    Receptionist --> UC_History
    Receptionist --> UC_AI

    Technician --> UC_Auth
    Technician --> UC_RO
    Technician --> UC_Inventory
    Technician --> UC_History
    Technician --> UC_AI

    Cashier --> UC_Auth
    Cashier --> UC_Billing
    Cashier --> UC_Report

    Manager --> UC_Auth
    Manager --> UC_Reception
    Manager --> UC_RO
    Manager --> UC_Inventory
    Manager --> UC_Billing
    Manager --> UC_Report
    Manager --> UC_Audit
    Manager --> UC_AI

    UC_AI --> AI_Service
```

---

## 2. BIỂU ĐỒ HOẠT ĐỘNG (ACTIVITY DIAGRAMS)

### 2.1. Tiếp nhận xe và Phân loại ưu tiên
```mermaid
flowchart TD
    Start([Xe vào xưởng]) --> TraCuu[Lễ tân tra cứu biển số xe]
    TraCuu --> CheckTonTai{Xe đã có hồ sơ?}
    CheckTonTai -- Chưa có --> TaoMoi[Đăng ký mới Khách hàng & Xe]
    CheckTonTai -- Đã có --> ChonXe[Tải hồ sơ phương tiện từ CSDL]
    TaoMoi --> GhiNhan[Ghi nhận Odometer, xăng, trầy xước]
    ChonXe --> GhiNhan
    GhiNhan --> AIDanhGia[Kích hoạt AI đánh giá triệu chứng]
    AIDanhGia --> CheckUuTien{Sự cố nguy hiểm / Khẩn cấp?}
    CheckUuTien -- Khẩn cấp --> GanCritical[Gán PRIORITY = CRITICAL & Giao KTV Trưởng]
    CheckUuTien -- Bình thường --> GanNormal[Gán PRIORITY = NORMAL & Xếp lịch thường]
    GanCritical --> TaoRO[Tạo Phiếu Sửa Chữa - Status: RECEIVED]
    GanNormal --> TaoRO
    TaoRO --> ChuyenXep[Chuyển xe vào cầu nâng kỹ thuật]
    ChuyenXep --> End([Hoàn tất tiếp nhận])
```

### 2.2. Luồng Sửa chữa và Nghiệm thu chất lượng KCS
```mermaid
flowchart TD
    Start([KTV nhận xe]) --> ChanDoan[Khảo sát & Nhập chẩn đoán chi tiết]
    ChanDoan --> DeXuat[Đề xuất Dịch vụ & Phụ tùng]
    DeXuat --> ChoDuyet{Khách duyệt báo giá?}
    ChoDuyet -- Từ chối --> Huy[Chuyển Status: CANCELLED]
    ChoDuyet -- Đồng ý --> KiemKho{Kiểm tra tồn kho phụ tùng?}
    KiemKho -- Không đủ tồn --> BaoThieu[Báo thiếu linh kiện & Rollback]
    KiemKho -- Đủ tồn kho --> TruKho[Trừ tồn kho tự động & Chuyển IN_REPAIR]
    TruKho --> ThiCong[KTV tiến hành sửa chữa xe]
    ThiCong --> KCSCheck[Chuyển KCS nghiệm thu - QUALITY_CHECK]
    KCSCheck --> DatChuan{KCS đạt tiêu chuẩn?}
    DatChuan -- Không đạt --> SuaLai[Trả về KTV sửa lại lỗi tồn đọng]
    SuaLai --> ThiCong
    DatChuan -- Đạt chuẩn --> HoanTat[Chuyển Status: COMPLETED]
    HoanTat --> SangHoaDon[Chuyển thông tin sang bộ phận Thu ngân]
    SangHoaDon --> End([Sẵn sàng giao xe])
    Huy --> End
```

---

## 3. BIỂU ĐỒ TUẦN TỰ (SEQUENCE DIAGRAMS)

### 3.1. Xác thực và Phân quyền (Login Sequence)
```mermaid
sequenceDiagram
    autonumber
    actor User as Nhân Viên
    participant Client as Web Client (login.html)
    participant Auth as Auth Router (/api/v1/auth/login)
    participant DB as SQLite (garage.db)

    User->>Client: Nhập username, password
    Client->>Auth: POST /auth/login (form-urlencoded)
    Auth->>DB: SELECT * FROM users WHERE username = ?
    DB-->>Auth: Trả về bản ghi User
    alt Mật khẩu sai hoặc tài khoản bị khóa
        Auth-->>Client: HTTP 401 Unauthorized / 403 Forbidden
        Client-->>User: Báo lỗi đăng nhập
    else Hợp lệ
        Auth->>Auth: bcrypt.verify(password, hashed_password)
        Auth->>Auth: jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        Auth-->>Client: HTTP 200 OK (access_token, role)
        Client->>Client: localStorage.setItem('garage_access_token', token)
        Client-->>User: Điều hướng vào admin.html theo Role
    end
```

### 3.2. Lập hóa đơn và Thanh toán VietQR
```mermaid
sequenceDiagram
    autonumber
    actor Cashier as Thu Ngân
    actor Customer as Khách Hàng
    participant Client as Web Client (admin.html)
    participant InvAPI as Invoice Router (/api/v1/invoices)
    participant VietQR as VietQR Napas Gateway (img.vietqr.io)
    participant DB as SQLite (garage.db)

    Cashier->>Client: Chọn RO đã COMPLETED, bấm "Lập Hóa Đơn"
    Client->>InvAPI: POST /api/v1/invoices {repair_order_id}
    InvAPI->>DB: Lấy ro_items, tự tính: subtotal, discount, vat, total
    InvAPI->>DB: INSERT INTO invoices (status: UNPAID, balance_due: total)
    DB-->>InvAPI: Lưu thành công (id: 50, total: 5,500,000)
    InvAPI-->>Client: Trả về Invoice #50
    
    Cashier->>Client: Bấm "Thanh Toán VietQR"
    Client->>VietQR: Yêu cầu sinh mã QR (Bank: TCB, STK: 4443338386, Amount: 5500000)
    VietQR-->>Client: Trả về ảnh mã QR Napas 24/7 động
    Client-->>Customer: Hiển thị mã VietQR trên màn hình thu ngân
    
    Customer->>Customer: Mở App Ngân hàng quét mã chuyển tiền
    Cashier->>Client: Nhận thông báo tiền vào tài khoản, bấm "Xác Nhận Đã Thu"
    Client->>InvAPI: POST /invoices/50/payments {amount: 5500000, method: 'BankTransfer'}
    InvAPI->>DB: UPDATE invoices SET paid_amount = 5500000, status = 'PAID'
    DB-->>InvAPI: Cập nhật thành công
    InvAPI-->>Client: HTTP 200 OK
    Client-->>Cashier: In hóa đơn giao khách hàng
```

---

## 4. BIỂU ĐỒ MÁY TRẠNG THÁI (STATE MACHINE DIAGRAM)

```mermaid
stateDiagram-v2
    [*] --> RECEIVED: Tiếp nhận xe
    RECEIVED --> INSPECTING: KTV bắt đầu kiểm tra
    INSPECTING --> QUOTATION_PENDING: Chẩn đoán xong
    QUOTATION_PENDING --> WAITING_CUSTOMER_APPROVAL: Đã gửi báo giá
    WAITING_CUSTOMER_APPROVAL --> APPROVED: Khách duyệt sửa
    WAITING_CUSTOMER_APPROVAL --> CANCELLED: Khách từ chối
    
    APPROVED --> IN_REPAIR: Bắt đầu sửa & Xuất kho
    IN_REPAIR --> WAITING_PARTS: Chờ phụ tùng đặc thù
    WAITING_PARTS --> IN_REPAIR: Phụ tùng đã về
    
    IN_REPAIR --> QUALITY_CHECK: KTV hoàn tất, chuyển KCS
    QUALITY_CHECK --> IN_REPAIR: KCS không đạt, sửa lại
    QUALITY_CHECK --> COMPLETED: KCS đạt chuẩn xuất xưởng
    
    COMPLETED --> INVOICED: Thu ngân lập hóa đơn
    INVOICED --> [*]: Thanh toán xong, đóng hồ sơ
    CANCELLED --> [*]: Đóng hồ sơ hủy
```

---

## 5. BIỂU ĐỒ LỚP (CLASS DIAGRAM)

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string hashed_password
        +string role
        +bool is_active
        +datetime created_at
    }

    class Customer {
        +int id
        +string customer_code
        +string full_name
        +string phone
        +string email
        +datetime deleted_at
    }

    class Vehicle {
        +int id
        +int customer_id
        +string license_plate
        +string brand
        +string model
        +int current_mileage
    }

    class RepairOrder {
        +int id
        +string order_code
        +int vehicle_id
        +int assigned_technician_id
        +string status
        +string symptoms
        +string diagnosis
        +decimal total_cost
    }

    class ROItem {
        +int id
        +int repair_order_id
        +string item_type
        +int service_id
        +int part_id
        +int quantity
        +decimal unit_price
    }

    class Service {
        +int id
        +string service_code
        +string name
        +decimal labor_cost
    }

    class Part {
        +int id
        +string part_code
        +string name
        +decimal sell_price
        +int stock_quantity
        +int min_stock_alert
    }

    class Invoice {
        +int id
        +string invoice_code
        +int repair_order_id
        +decimal subtotal
        +decimal vat_rate
        +decimal total_amount
        +decimal paid_amount
        +string status
    }

    class Payment {
        +int id
        +int invoice_id
        +decimal amount
        +string payment_method
        +datetime payment_date
    }

    Customer "1" --> "0..*" Vehicle : sở hữu
    Vehicle "1" --> "0..*" RepairOrder : sửa chữa
    RepairOrder "1" --> "0..*" ROItem : bao gồm
    ROItem "0..*" --> "0..1" Service : công thợ
    ROItem "0..*" --> "0..1" Part : linh kiện
    RepairOrder "1" --> "0..1" Invoice : thanh toán
    Invoice "1" --> "0..*" Payment : đợt nạp tiền
    User "1" --> "0..*" RepairOrder : KTV phụ trách
```

---

## 6. BIỂU ĐỒ THÀNH PHẦN (COMPONENT DIAGRAM)

```mermaid
graph TD
    subgraph "Client Layer"
        HTML[HTML5 Templates]
        CSS[Design System CSS]
        JS[Client Controller app.js]
        LocalEngine[(LocalStorage Mock Engine)]
    end

    subgraph "FastAPI Server"
        APIGateway[FastAPI Router Gateway]
        AuthModule[Auth & RBAC Middleware]
        StateMachine[Repair Order State Machine]
        PricingEngine[Deterministic Pricing Engine]
        StockGuard[Inventory Transaction Guard]
        AIOrchestrator[AI Provider Orchestrator]
    end

    subgraph "External & Persistence Layer"
        GeminiAPI[Google Gemini 2.5 API]
        VietQRAPI[VietQR Napas Gateway]
        SQLiteDB[(SQLite Database: garage.db)]
    end

    HTML --> JS
    CSS --> HTML
    JS <--> LocalEngine
    JS -- REST API / JWT --> APIGateway

    APIGateway --> AuthModule
    AuthModule --> StateMachine
    AuthModule --> PricingEngine
    AuthModule --> StockGuard
    AuthModule --> AIOrchestrator

    AIOrchestrator --> GeminiAPI
    PricingEngine --> VietQRAPI
    StateMachine --> SQLiteDB
    StockGuard --> SQLiteDB
    PricingEngine --> SQLiteDB
```

---

## 7. BIỂU ĐỒ TRIỂN KHAI (DEPLOYMENT DIAGRAM)

```mermaid
graph TD
    subgraph "Client Devices (Browser)"
        PC[Máy Tính Bàn Lễ Tân / Thu Ngân]
        Tablet[Máy Tính Bảng Android Kỹ Thuật Viên]
        Phone[Điện Thoại Khách Hàng]
    end

    subgraph "Docker Host / Cloud Server"
        Nginx[Nginx Reverse Proxy / Port 80/443]
        FastAPI_App[FastAPI Uvicorn Container / Port 8000]
        Persistent_Volume[(Docker Volume: /data/garage.db)]
    end

    subgraph "External Cloud Services"
        GeminiCloud[Google AI Cloud Engine]
        NapasCloud[Napas VietQR Service]
    end

    PC -- HTTPS --> Nginx
    Tablet -- HTTPS / Local WiFi --> Nginx
    Phone -- HTTPS 4G/5G --> Nginx

    Nginx --> FastAPI_App
    FastAPI_App <--> Persistent_Volume
    FastAPI_App -- TLS/gRPC --> GeminiCloud
    FastAPI_App -- HTTPS REST --> NapasCloud
```
