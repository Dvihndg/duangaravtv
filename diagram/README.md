# Danh Sách Sơ Đồ Kỹ Thuật Hệ Thống GarageAI (PlantUML & Mermaid)

Thư mục này chứa 7 sơ đồ kỹ thuật PlantUML (`.puml`) và tài liệu mô tả đầy đủ kiến trúc, thực thể cơ sở dữ liệu, Use Case và luồng hoạt động của hệ thống.

---

## 📁 Cấu Trúc Thư Mục `diagram/`

```text
diagram/
├── 01_use-case-overview.puml
├── 02_activity-uc001-priority-assessment.puml
├── 03_sequence-uc001-priority-assessment.puml
├── 04_activity-uc002-model-training.puml
├── 05_sequence-uc002-model-training.puml
├── 06_component-architecture.puml
├── 07_class-domain-model.puml
└── README.md
```

---

## 📋 Chi Tiết Danh Sách 7 Sơ Đồ

### 1. `01_use-case-overview.puml`
- **Loại sơ đồ:** Use Case Diagram
- **Nội dung:** Tổng quan các Use Case chính của hệ thống (Đăng ký tiếp nhận, chẩn đoán AI, lập báo giá nháp, thanh toán VietQR, quản lý kho & báo cáo kinh doanh).

### 2. `02_activity-uc001-priority-assessment.puml`
- **Loại sơ đồ:** Activity Diagram
- **Nội dung:** Luồng hoạt động tiếp nhận xe & phân tích mức độ ưu tiên kỹ thuật (Priority Assessment Workflow).

### 3. `03_sequence-uc001-priority-assessment.puml`
- **Loại sơ đồ:** Sequence Diagram
- **Nội dung:** Trình tự tương tác giữa Lễ tân, Web App, FastAPI Server, Gemini AI Engine và SQLite Database khi tiếp nhận xe.

### 4. `04_activity-uc002-model-training.puml`
- **Loại sơ đồ:** Activity Diagram
- **Nội dung:** Quy trình tối ưu & đo lường độ chính xác của AI Model (Model Evaluation & Zero Price Variance Check).

### 5. `05_sequence-uc002-model-training.puml`
- **Loại sơ đồ:** Sequence Diagram
- **Nội dung:** Trình tự xuất báo cáo đánh giá đo lường hệ thống AI (Top-1 Accuracy, Parts Precision, Latency, Token Cost).

### 6. `06_component-architecture.puml`
- **Loại sơ đồ:** Component Architecture Diagram
- **Nội dung:** Kiến trúc các thành phần của hệ thống (Web Client, FastAPI Gateway Router, Pricing Engine, AI Service & SQLite Database).

### 7. `07_class-domain-model.puml`
- **Loại sơ đồ:** Class Domain Model Diagram
- **Nội dung:** Sơ đồ các lớp miền nghiệp vụ (Customer, Vehicle, RepairOrder, RepairOrderItem, Service, Part, Invoice, Payment, AILog) và quan hệ giữa chúng.

---

## 🛠️ Hướng Dẫn Xem & Xuất Ảnh Sơ Đồ PlantUML
1. Mở file `.puml` bất kỳ trong VS Code với extension **PlantUML**.
2. Bấm tổ hợp phím `Alt + D` để xem xem trước (Preview) sơ đồ trực tiếp.
3. Hoặc xuất ảnh PNG/SVG bằng phím `Ctrl + Shift + P` -> chọn **PlantUML: Export Current Diagram**.
