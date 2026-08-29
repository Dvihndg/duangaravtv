# Sơ Đồ Kỹ Thuật Hệ Thống Quản Lý Garage Ô Tô Tích Hợp AI (GarageAI Engine)

Thư mục này chứa toàn bộ sơ đồ kiến trúc, sơ đồ thực thể cơ sở dữ liệu (ERD) và sơ đồ luồng hoạt động (Sequence & Workflow Diagrams) của hệ thống.

---

## 1. Sơ Đồ Kiến Trúc Hệ Thống (System Architecture Diagram)

```mermaid
graph TD
    subgraph Client_Layer ["Client Layer (Giao diện Người dùng)"]
        UI["Web App (HTML5 / Vanilla JS / CSS3)"]
        ChatWidget["Trợ lý GarageAI Chat Widget"]
        RoleSwitcher["Role Switcher (Lễ tân, KTV, Quản lý, Thu ngân)"]
    end

    subgraph API_Gateway ["Backend API Gateway (FastAPI)"]
        AuthRouter["Auth Router (JWT Authentication)"]
        CustomerRouter["Customers & Vehicles Router"]
        RORouter["Repair Orders Router"]
        InvoiceRouter["Invoices & VietQR Payments Router"]
        AIRouter["AI Assistant Router"]
    end

    subgraph Service_Engine ["Business Logic & AI Engine"]
        PriceEngine["Deterministic Pricing Engine (Python)"]
        AIService["Gemini 2.5 Flash AI Engine"]
        QREngine["VietQR Napas 247 Generator"]
    end

    subgraph Database_Layer ["Storage Layer"]
        DB[(SQLite / garage.db)]
        AILogDB[(AI Audit Logs)]
    end

    UI -->|HTTP / JSON API| API_Gateway
    ChatWidget -->|POST /api/v1/ai/assistant| AIRouter
    RoleSwitcher -->|Bearer Token| AuthRouter

    API_Gateway --> Service_Engine
    AIRouter --> AIService
    RORouter --> PriceEngine
    InvoiceRouter --> QREngine

    Service_Engine --> Database_Layer
```

---

## 2. Sơ Đồ Thực Thể Cơ Sở Dữ Liệu (ERD Diagram)

```mermaid
erDiagram
    CUSTOMERS ||--o{ VEHICLES : "sở hữu"
    VEHICLES ||--o{ APPOINTMENTS : "đặt lịch"
    VEHICLES ||--o{ REPAIR_ORDERS : "tiếp nhận"
    REPAIR_ORDERS ||--o{ REPAIR_ORDER_ITEMS : "chứa"
    SERVICES ||--o{ REPAIR_ORDER_ITEMS : "áp dụng"
    PARTS ||--o{ REPAIR_ORDER_ITEMS : "sử dụng"
    REPAIR_ORDERS ||--o| INVOICES : "phát sinh"
    INVOICES ||--o{ PAYMENTS : "thanh toán"
    USERS ||--o{ REPAIR_ORDERS : "quản lý"
    USERS ||--o{ PAYMENTS : "xác nhận"
    USERS ||--o{ AI_LOGS : "thực hiện"

    CUSTOMERS {
        int id PK
        string full_name
        string phone
        string address
        datetime created_at
    }

    VEHICLES {
        int id PK
        int customer_id FK
        string license_plate
        string brand
        string model
        int year
    }

    REPAIR_ORDERS {
        int id PK
        int vehicle_id FK
        string code
        int mileage_at_reception
        string initial_symptoms
        string technical_diagnosis
        float final_cost
        string status
    }

    REPAIR_ORDER_ITEMS {
        int id PK
        int repair_order_id FK
        int service_id FK
        int part_id FK
        string name
        string item_type
        float quantity
        float unit_price
        float labor_cost
        float total_price
    }

    INVOICES {
        int id PK
        string invoice_number
        int repair_order_id FK
        float total_amount
        float paid_amount
        string status
    }

    PAYMENTS {
        int id PK
        int invoice_id FK
        string payment_method
        float amount
        datetime payment_date
    }

    AI_LOGS {
        int id PK
        int user_id FK
        string feature_used
        string prompt
        string raw_response
        float price_variance
    }
```

---

## 3. Sơ Đồ Luồng Hoạt Động Trợ Lý GarageAI (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng / Lễ tân
    participant UI as Giao diện Trợ lý GarageAI
    participant Backend as FastAPI Server
    participant Gemini as Gemini AI Engine
    participant DB as Database SQLite

    User->>UI: Nhập câu hỏi (Ví dụ: "Xe máy 5.000 km bảo dưỡng gì?")
    UI->>UI: Hiển thị câu hỏi (User Bubble) & Loading Indicator
    UI->>Backend: POST /api/v1/ai/assistant { question }
    Backend->>DB: Truy vấn dữ liệu xe & danh mục dịch vụ chuẩn
    DB-->>Backend: Trả về thông tin niêm yết DB
    Backend->>Gemini: Gửi Prompt + Context dữ liệu niêm yết
    Gemini-->>Backend: Trả về kết quả phân tích & gợi ý
    Backend->>Backend: Ghi log giao dịch vào AI_LOGS (Kiểm tra Sai lệch giá = 0%)
    Backend-->>UI: JSON { output, model_used }
    UI->>UI: Stream kết quả định dạng Markdown vào cửa sổ chat
```
