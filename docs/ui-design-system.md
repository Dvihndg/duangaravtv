# GARAGE VTV AI MANAGEMENT SYSTEM — UI/UX DESIGN SYSTEM SPECIFICATION

**Document Version:** 1.0.0  
**Project:** Garage VTV AI Management System  
**Path:** `docs/ui-design-system.md`  

---

## 1. Executive Summary & Design Philosophy

The **GARAGE VTV AI MANAGEMENT SYSTEM** follows a consistent, professional, modern automotive UI/UX design system inspired by high-end automotive SaaS platforms (e.g., Manus AI Engine, Porsche/Tesla OS UI).

### Core Design Principles

1. **Simplicity First**: Clean, focused interface without unnecessary decorations, excessive animations, or visual clutter. Usability takes priority over decoration.
2. **Consistency Across Modules**: Every page, modal, button, badge, input, and table consumes centralized design tokens.
3. **Information Hierarchy**: Primary information is visually dominant (H1/H2 font sizes, bold weights, high contrast), while secondary details remain subordinate.
4. **Contrast & Visual Clarity**: High-contrast text/background ratios, deliberate whitespace, and multi-modal status indicators (Color + Text + Icon).
5. **Responsive & Mobile-First**: Mobile targets (320px+), Tablet targets (768px+), Desktop targets (1024px/1280px+).

---

## 2. Centralized Design Tokens

All styles consume CSS custom properties defined in `styles.css`.

### 2.1 Color System

#### Dark Mode (Default Theme: `data-theme="dark"`)
```css
:root {
  --bg-primary: #090d16;
  --bg-sidebar: #0f172a;
  --bg-card: #131c2e;
  --bg-card-hover: #1e293b;
  --bg-input: #0b1120;
  --border-color: #1e293b;
  --border-subtle: #172033;
  
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-light: #64748b;

  --accent-primary: #3b82f6;
  --accent-primary-hover: #2563eb;
  --accent-cyan: #06b6d4;
  --accent-purple: #8b5cf6;
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;

  --gradient-brand: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  --gradient-ai: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 14px rgba(0,0,0,0.5);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.6);
  
  --radius-lg: 16px;
  --radius-md: 12px;
  --radius-sm: 8px;
}
```

#### Light Mode Theme (`data-theme="light"`)
```css
[data-theme="light"] {
  --bg-primary: #f8fafc;
  --bg-sidebar: #ffffff;
  --bg-card: #ffffff;
  --bg-card-hover: #f1f5f9;
  --bg-input: #f8fafc;
  --border-color: #e2e8f0;
  --border-subtle: #f1f5f9;

  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-light: #94a3b8;

  --accent-primary: #2563eb;
  --accent-primary-hover: #1d4ed8;
  --accent-cyan: #0891b2;
  --accent-purple: #7c3aed;
  --accent-emerald: #059669;
  --accent-amber: #d97706;
  --accent-rose: #e11d48;
}
```

---

## 3. Typography System

The system uses Google Fonts `Plus Jakarta Sans` for UI elements and numbers, and `Outfit` for headers.

| Level | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| **H1** | 1.5rem (24px) | 800 | 1.2 | Main Page Titles |
| **H2** | 1.25rem (20px) | 700 | 1.25 | Section Titles |
| **H3** | 1.1rem (17.6px) | 700 | 1.3 | Card / Table Header Titles |
| **Body Main** | 0.9rem (14.4px) | 500 / 600 | 1.4 | Primary Text & Content |
| **Caption / Subtext** | 0.78rem (12.5px) | 500 | 1.35 | Secondary Labels, Timestamps |
| **Metric Value** | 2.2rem (35.2px) | 800 | 1.1 | KPI Numbers |

---

## 4. Spacing & Radius Scale

```css
Spacing Scale: 4px | 8px | 12px | 16px | 24px | 32px | 48px | 64px
Border Radius: 8px (Small) | 12px (Medium) | 16px (Large Cards) | 99px (Pill Badges)
```

---

## 5. Component Specifications

### 5.1 Button Hierarchy

1. **Primary Button (`.btn-primary`)**:
   - Background: `--accent-primary` (`#2563eb` / `#3b82f6`)
   - Text: White, Weight: 700
   - Usage: Main Call-To-Action on screen (e.g. `[ SEND REQUEST ]`, `[ CREATE REPAIR ORDER ]`).

2. **Secondary Button (`.btn-secondary`)**:
   - Background: Transparent with `--border-color` border.
   - Usage: Auxiliary options (e.g. `[ Back ]`, `[ View Details ]`, `[ Cancel ]`).

3. **Destructive Button (`.btn-danger`)**:
   - Background: `--accent-rose` / Red (`#f43f5e` / `#e11d48`).
   - Usage: Destructive irreversible actions (e.g. `[ Reject ]`, `[ Delete ]`, `[ Cancel Order ]`).

4. **AI Assistant Button (`.ai-tab`)**:
   - Background: `rgba(124, 58, 237, 0.25)` with purple glowing border (`rgba(168, 85, 247, 0.4)`).
   - Usage: AI Assistant trigger.

### 5.2 Status Badges (Multi-modal: Color + Text + Icon)

Never rely on color alone to communicate status.

| Domain | Status Code | Visual Text | Icon | Color Badge Theme |
|---|---|---|---|---|
| **Appointment** | `PENDING` | `Chờ Tiếp Nhận` | `🗓️` | Amber (`#f59e0b`) |
| **Appointment** | `CONFIRMED` | `Đã Xác Nhận` | `✓` | Cyan (`#06b6d4`) |
| **Appointment** | `COMPLETED` | `Hoàn Thành` | `✅` | Emerald (`#10b981`) |
| **Repair Order** | `RECEIVED` | `Đã Tiếp Nhận` | `🚗` | Blue (`#3b82f6`) |
| **Repair Order** | `IN_REPAIR` | `Đang Sửa Chữa` | `🔧` | Emerald (`#10b981`) |
| **Repair Order** | `CANCELLED` | `Đã Hủy` | `×` | Rose (`#f43f5e`) |
| **Invoice** | `UNPAID` | `! Chưa Thanh Toán` | `!` | Amber (`#f59e0b`) |
| **Invoice** | `PAID` | `✓ Đã Thanh Toán` | `✓` | Emerald (`#10b981`) |

---

## 6. Layout Architectures

### 6.1 Customer Public Portal (`/customer` / `customer.html`)
- **Focus**: Mobile-First, single-column, large touch targets, simplified form inputs, immediate feedback upon submission.
- **Form Structure**:
  1. Customer Contact Info (`Full Name *`, `Phone Number *`, `Email`, `Address`)
  2. Vehicle Specs (`License Plate *`, `Brand *`, `Model *`, `Year`, `Current Mileage`)
  3. Service Request (`Service Type *`, `Problem Description`, `Preferred Date & Time`, `Notes`)

### 6.2 Admin Dashboard (`/admin` / `admin.html`)
- **Layout**: Fixed Collapsible Sidebar + Sticky Header + 4-KPI Grid + 2-Column Middle Grid (Revenue Chart + Recent Activity Feed) + Bottom Data Table.
- **Sidebar Groups**:
  - `TỔNG QUAN`: `Dashboard`, `Lịch Hẹn & Tiếp Nhận`, `Phiếu Sửa Chữa`
  - `DANH MỤC & KHÁCH`: `Quản Lý Yêu Cầu`, `Khách Hàng & Xe`, `Đăng Ký Khách Hàng`, `Kho Phụ Tùng & Dịch Vụ`, `Hóa Đơn & Thanh Toán`
  - `CÔNG CỤ AI`: `Trợ Lý AI Garage`

---

## 7. AI UI Integration

AI features MUST appear seamlessly integrated into the application workflow rather than as an isolated chatbot widget.

1. **AI Output Tagging**: All AI-generated suggestions, explanations, or draft quotes MUST be explicitly tagged with `🤖 AI Generated (Garage VTV Engine Pro)`.
2. **Staff Override Boundary**: AI outputs provide draft estimates only (`AI KHÔNG tự ý chốt giá cuối cùng`). Staff members maintain final approval authority.
3. **Security Boundary**: All untrusted customer data is wrapped in `<UNTRUSTED_CUSTOMER_DATA>` delimiters to prevent prompt injection execution.

---

## 8. State Feedback Guidelines

- **Loading State**: Displays skeleton loaders or disabled button spinners (e.g. `Đang xử lý...`).
- **Empty State**: Displays clear icon, explanatory title (e.g. `Chưa có lịch hẹn nào`), and a primary CTA `[ Tạo Lịch Hẹn ]`.
- **Error State**: User-friendly Vietnamese messages (e.g. `Không thể lưu phiếu sửa chữa. Vui lòng thử lại.`).
- **Success State**: Clear confirmation banner (e.g. `✓ Đã gửi yêu cầu thành công! Mã: REQ-20260905-0001`).

---

## 9. Accessibility & Responsive Breakpoints

- **Breakpoints**: Mobile (`320px+`), Tablet (`768px+`), Laptop/Desktop (`1024px+` & `1280px+`).
- **Contrast**: Minimum 4.5:1 ratio for text against background in both Light and Dark themes.
- **Touch Targets**: Minimum 44px x 44px clickable area on mobile screens.

---

## 10. Verification Priority Checklist

1. [x] Usability over decorative effects
2. [x] Centralized design tokens in `styles.css`
3. [x] Multi-modal status badges (Color + Text + Icon)
4. [x] Mobile-first customer experience
5. [x] Responsive layout without horizontal scrollbars
6. [x] Safe untrusted data boundaries for AI prompts
