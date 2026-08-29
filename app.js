const API_BASE = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")) 
  ? "http://127.0.0.1:8000/api/v1" 
  : "/api/v1";

// Application State
let currentState = {
  currentRole: "receptionist",
  token: null,
  activeView: "customer-requests",
  customers: [],
  vehicles: [],
  appointments: [],
  repairOrders: [],
  services: [],
  parts: [],
  invoices: [],
  activeROId: null,
  activeAIContext: { repair_order_id: null, vehicle_id: null }
};

// Role Credentials Mapping for fast switching during demo
const ROLE_CREDENTIALS = {
  manager: { username: "admin", password: "admin123" },
  receptionist: { username: "letan", password: "letan123" },
  technician: { username: "kythuat", password: "tech123" },
  cashier: { username: "thungan", password: "cashier123" }
};

// Fault-Tolerant Application Initialization
document.addEventListener("DOMContentLoaded", async () => {
  try { setupTheme(); } catch (e) { console.error("setupTheme:", e); }
  try { checkAuthPermission(); } catch (e) { console.error("checkAuthPermission:", e); }
  try { setupNavigation(); } catch (e) { console.error("setupNavigation:", e); }
  try { setupRoleSwitcher(); } catch (e) { console.error("setupRoleSwitcher:", e); }
  try { setupFilterListeners(); } catch (e) { console.error("setupFilterListeners:", e); }
  try { initDatepickers(); } catch (e) { console.error("initDatepickers:", e); }

  const path = window.location.pathname.toLowerCase();
  const isCustomerPage = path.endsWith("index.html") || path.endsWith("customer.html") || path.endsWith("/");
  
  if (!isCustomerPage) {
    try { await loginAsCurrentRole(); } catch (e) { console.error("loginAsCurrentRole:", e); }
    try { await populateVehicleDropdowns(); } catch (e) { console.error("populateVehicleDropdowns:", e); }
    try { initSSERealtimeStream(); } catch (e) { console.error("initSSERealtimeStream:", e); }
  }

  try { setupGlobalEventDelegation(); } catch (e) { console.error("setupGlobalEventDelegation:", e); }
});

function setupTheme() {
  const savedTheme = localStorage.getItem("garage_theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("garage_theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const icon = document.getElementById("theme-icon");
  if (icon) {
    icon.className = theme === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
  }
}

// Authorization Guard & 404 Access Denied Handler
function checkAuthPermission() {
  const role = localStorage.getItem("garage_user_role");
  const isLoggedIn = localStorage.getItem("garage_is_logged_in") === "true";
  const internalRoles = ["manager", "receptionist", "technician", "cashier"];

  const path = window.location.pathname.toLowerCase();
  
  // Enforce internal authorization check specifically when accessing admin.html or /admin
  if (path.endsWith("admin.html") || path.endsWith("/admin")) {
    if (!isLoggedIn || !internalRoles.includes(role)) {
      window.location.href = "login.html";
      return false;
    }
  }

  if (internalRoles.includes(role)) {
    currentState.currentRole = role;
    const roleSelect = document.getElementById("role-select");
    if (roleSelect) roleSelect.value = role;
  }

  return true;
}

function logoutUser() {
  localStorage.removeItem("garage_user_role");
  localStorage.removeItem("garage_is_logged_in");
  window.location.href = "login.html";
}

// Flatpickr Datepicker Initialization Helper
function initDatepickers() {
  if (typeof flatpickr === "undefined") return;

  // Set Vietnamese locale globally if available
  if (flatpickr.l10ns && flatpickr.l10ns.vn) {
    flatpickr.localize(flatpickr.l10ns.vn);
  }

  // 1. Booking / Appointment Datetime Pickers (with time & minDate = today)
  const dateTimeSelectors = ["#apt-date", "#cp-apt-date"];
  dateTimeSelectors.forEach(selector => {
    const el = document.querySelector(selector);
    if (el && !el._flatpickr) {
      flatpickr(el, {
        enableTime: true,
        dateFormat: "d/m/Y H:i",
        time_24hr: true,
        minDate: "today",
        defaultHour: 8,
        defaultMinute: 0,
        locale: flatpickr.l10ns?.vn || "default"
      });
    }
  });

  // 2. Filter Date Pickers (Date only)
  const dateSelectors = ["#appointment-date-filter", "#ro-date-from", "#ro-date-to", "#invoice-date-from", "#invoice-date-to"];
  dateSelectors.forEach(selector => {
    const el = document.querySelector(selector);
    if (el && !el._flatpickr) {
      flatpickr(el, {
        dateFormat: "d/m/Y",
        locale: flatpickr.l10ns?.vn || "default"
      });
    }
  });
}

function openModal(modalId, title = null, content = null) {
  const modal = document.getElementById(modalId);
  if (modal) {
    if (title) {
      const titleEl = document.getElementById(`${modalId}-title`) || modal.querySelector(".modal-header h3");
      if (titleEl) titleEl.innerHTML = title;
    }
    if (content) {
      const bodyEl = document.getElementById(`${modalId}-body`) || modal.querySelector(".modal-card > div:not(.modal-header)");
      if (bodyEl) bodyEl.innerHTML = content;
    }
    modal.classList.add("active");
    modal.style.display = "flex";
    setTimeout(() => initDatepickers(), 50);
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("active");
    modal.style.display = "none";
  }
}

// Auth & Role Handler
async function loginAsCurrentRole() {
  if (isBackendAvailable === false) {
    currentState.token = "demo-offline-jwt-token";
    return;
  }
  const creds = ROLE_CREDENTIALS[currentState.currentRole];
  try {
    const formData = new URLSearchParams();
    formData.append("username", creds.username);
    formData.append("password", creds.password);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 200);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      currentState.token = data.access_token;
      isBackendAvailable = true;
    } else {
      currentState.token = "demo-offline-jwt-token";
    }
  } catch (err) {
    isBackendAvailable = false;
    console.warn("Chế độ Demo Web Offline: Tự động kích hoạt JWT token mô phỏng.");
    currentState.token = "demo-offline-jwt-token";
  }
}

// Detect static hosting environment (GitHub Pages, Netlify, Vercel, HTTPS live deployment)
const isLocalhostHost = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
const API_BASE = isLocalhostHost ? "http://127.0.0.1:8000/api/v1" : "/api/v1";
let isBackendAvailable = true;

// Helper fetch wrapper connecting directly to Online Backend API
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (currentState.token) {
    headers["Authorization"] = `Bearer ${currentState.token}`;
  }
  headers["Content-Type"] = "application/json";

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout for Vercel Serverless cold start

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: "Lỗi kết nối máy chủ" }));
      throw new Error(errData.detail || "Thao tác thất bại");
    }
    isBackendAvailable = true;
    return await res.json();
  } catch (err) {
    console.warn(`[Online Backend Notice] Falling back to local engine for ${endpoint}:`, err);
    return getOfflineMockResponse(endpoint, options);
  }
}

// ============================================================
// LOCAL STORAGE DATABASE ENGINE (Offline Persistent Layer)
// All customer form submissions stored & retrieved from here
// ============================================================
const DB_KEYS = {
  customers:        "vtv_db_customers",
  vehicles:         "vtv_db_vehicles",
  appointments:     "vtv_db_appointments",
  repairOrders:     "vtv_db_repair_orders",
  invoices:         "vtv_db_invoices",
  customerRequests: "vtv_db_customer_requests",
  services:         "vtv_db_services",
  parts:            "vtv_db_parts"
};

// Purge all old demo data from localStorage (Keep Services & Parts catalog intact)
if (!localStorage.getItem("vtv_demo_data_purged_v2")) {
  localStorage.removeItem(DB_KEYS.customers);
  localStorage.removeItem(DB_KEYS.vehicles);
  localStorage.removeItem(DB_KEYS.appointments);
  localStorage.removeItem(DB_KEYS.repairOrders);
  localStorage.removeItem(DB_KEYS.invoices);
  localStorage.removeItem(DB_KEYS.customerRequests);
  localStorage.setItem("vtv_demo_data_purged_v2", "true");
}

function dbRead(key) {
  try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch { return []; }
}

function dbWrite(key, data) {
  try { localStorage.setItem(key, JSON.stringify(data)); } catch (e) { console.warn("Storage full:", e); }
}

function dbNextId(key) {
  const list = dbRead(key);
  return list.length > 0 ? Math.max(...list.map(r => r.id || 0)) + 1 : 1;
}

function dbPadCode(prefix, n) {
  return `${prefix}-${String(n).padStart(6, '0')}`;
}

// Auto-generate REQ-YYYYMMDD-XXXX code
function dbNextRequestCode() {
  const today = new Date();
  const d = String(today.getDate()).padStart(2, '0');
  const m = String(today.getMonth() + 1).padStart(2, '0');
  const y = today.getFullYear();
  const dateStr = `${y}${m}${d}`;
  const prefix = `REQ-${dateStr}-`;
  const existing = dbRead(DB_KEYS.customerRequests).filter(r => (r.requestCode || "").startsWith(prefix));
  const seq = existing.length + 1;
  return `${prefix}${String(seq).padStart(4, '0')}`;
}

// Mock fallback provider for Web Demo
function getOfflineMockResponse(endpoint, options) {
  const method = (options.method || "GET").toUpperCase();
  let body = {};
  try { body = JSON.parse(options.body || "{}"); } catch { body = {}; }

  // ----- CUSTOMER REQUESTS -----
  if (endpoint === "/customer-requests") {
    if (method === "GET") return dbRead(DB_KEYS.customerRequests);
    if (method === "POST") {
      // Anti-spam: same phone + plate within 60s
      const now = new Date();
      const existing = dbRead(DB_KEYS.customerRequests);
      const recentSpam = existing.find(r => {
        if (r.phone !== body.phone || r.licensePlate !== body.licensePlate) return false;
        const created = new Date(r.createdAt);
        return (now - created) < 60000;
      });
      if (recentSpam) throw new Error(`Yêu cầu đã được tiếp nhận (Mã: ${recentSpam.requestCode}). Vui lòng đợi!`);

      // Auto-create or reuse Customer
      let customers = dbRead(DB_KEYS.customers);
      let customer = customers.find(c => c.phone === body.phone);
      if (!customer) {
        const cId = dbNextId(DB_KEYS.customers);
        customer = {
          id: cId, full_name: body.fullName, phone: body.phone,
          email: body.email || "", address: body.address || "",
          customer_code: dbPadCode("KH", cId), created_at: now.toISOString()
        };
        customers.push(customer);
        dbWrite(DB_KEYS.customers, customers);
      }

      // Auto-create or reuse Vehicle
      let vehicles = dbRead(DB_KEYS.vehicles);
      let vehicle = vehicles.find(v => v.license_plate === body.licensePlate);
      if (!vehicle) {
        const vId = dbNextId(DB_KEYS.vehicles);
        vehicle = {
          id: vId, customer_id: customer.id, license_plate: body.licensePlate,
          brand: body.vehicleBrand, model: body.vehicleModel,
          year: body.manufactureYear || 2020, current_mileage: body.currentMileage || 0,
          created_at: now.toISOString()
        };
        vehicles.push(vehicle);
        dbWrite(DB_KEYS.vehicles, vehicles);
      } else if (body.currentMileage && body.currentMileage > vehicle.current_mileage) {
        vehicle.current_mileage = body.currentMileage;
        dbWrite(DB_KEYS.vehicles, vehicles);
      }

      // Create CustomerRequest
      const reqId = dbNextId(DB_KEYS.customerRequests);
      const reqCode = dbNextRequestCode();
      const newReq = {
        id: reqId, requestCode: reqCode,
        fullName: body.fullName, phone: body.phone,
        email: body.email || null, address: body.address || null,
        licensePlate: body.licensePlate, vehicleBrand: body.vehicleBrand,
        vehicleModel: body.vehicleModel, manufactureYear: body.manufactureYear || 2020,
        currentMileage: body.currentMileage || 0,
        serviceType: body.serviceType, description: body.description || null,
        preferredDate: body.preferredDate || null, preferredTime: body.preferredTime || "09:00",
        note: body.note || null,
        status: "Pending", adminNote: null,
        customerId: customer.id, vehicleId: vehicle.id,
        assignedEmployeeId: null, assignedEmployeeName: null,
        createdAt: now.toISOString(), updatedAt: now.toISOString()
      };
      const reqs = dbRead(DB_KEYS.customerRequests);
      reqs.push(newReq);
      dbWrite(DB_KEYS.customerRequests, reqs);
      return newReq;
    }
  }

  // Customer Requests by Code (public tracking)
  const codeMatch = endpoint.match(/^\/customer-requests\/code\/(.+)$/);
  if (codeMatch) {
    const code = codeMatch[1].toUpperCase();
    const req = dbRead(DB_KEYS.customerRequests).find(r => r.requestCode === code);
    if (!req) throw new Error("Không tìm thấy mã yêu cầu này trên hệ thống!");
    return req;
  }

  // Customer Requests by ID (PATCH status, POST note, GET detail)
  const reqIdMatch = endpoint.match(/^\/customer-requests\/(\d+)(\/.*)?$/);
  if (reqIdMatch) {
    const rId = parseInt(reqIdMatch[1]);
    const subPath = reqIdMatch[2] || "";
    const reqs = dbRead(DB_KEYS.customerRequests);
    const idx = reqs.findIndex(r => r.id === rId);
    if (idx === -1) throw new Error("Không tìm thấy yêu cầu dịch vụ!");

    if (method === "GET") return reqs[idx];

    if (method === "PATCH" && subPath === "/status") {
      reqs[idx].status = body.status;
      reqs[idx].updatedAt = new Date().toISOString();
      dbWrite(DB_KEYS.customerRequests, reqs);
      return reqs[idx];
    }
    if (method === "POST" && subPath === "/note") {
      reqs[idx].adminNote = body.admin_note;
      reqs[idx].updatedAt = new Date().toISOString();
      dbWrite(DB_KEYS.customerRequests, reqs);
      return reqs[idx];
    }
    if (method === "POST" && subPath === "/assign") {
      reqs[idx].assignedEmployeeId = body.assigned_employee_id;
      reqs[idx].updatedAt = new Date().toISOString();
      dbWrite(DB_KEYS.customerRequests, reqs);
      return reqs[idx];
    }
    if (method === "DELETE") {
      reqs.splice(idx, 1);
      dbWrite(DB_KEYS.customerRequests, reqs);
      return { success: true };
    }
    return reqs[idx];
  }

  // ----- CUSTOMERS -----
  if (endpoint === "/customers") {
    if (method === "GET") return dbRead(DB_KEYS.customers);
    if (method === "POST") {
      const existing = dbRead(DB_KEYS.customers);
      let cust = existing.find(c => c.phone === body.phone);
      if (!cust) {
        const cId = dbNextId(DB_KEYS.customers);
        cust = {
          id: cId, full_name: body.full_name || body.fullName,
          phone: body.phone, email: body.email || "",
          address: body.address || "", customer_code: dbPadCode("KH", cId),
          created_at: new Date().toISOString()
        };
        existing.push(cust);
        dbWrite(DB_KEYS.customers, existing);
      }
      return cust;
    }
  }

  // Customer by ID
  const custIdMatch = endpoint.match(/^\/customers\/(\d+)$/);
  if (custIdMatch) {
    const cId = parseInt(custIdMatch[1]);
    const customers = dbRead(DB_KEYS.customers);
    if (method === "PUT" || method === "PATCH") {
      const idx = customers.findIndex(c => c.id === cId);
      if (idx >= 0) { Object.assign(customers[idx], body); dbWrite(DB_KEYS.customers, customers); return customers[idx]; }
    }
    if (method === "DELETE") {
      const idx = customers.findIndex(c => c.id === cId);
      if (idx >= 0) { customers.splice(idx, 1); dbWrite(DB_KEYS.customers, customers); }
      return { success: true };
    }
    return customers.find(c => c.id === cId) || null;
  }

  // ----- VEHICLES -----
  if (endpoint === "/vehicles") {
    if (method === "GET") return dbRead(DB_KEYS.vehicles);
    if (method === "POST") {
      const existing = dbRead(DB_KEYS.vehicles);
      let veh = existing.find(v => v.license_plate === body.license_plate);
      if (!veh) {
        const vId = dbNextId(DB_KEYS.vehicles);
        veh = {
          id: vId, customer_id: body.customer_id, license_plate: body.license_plate,
          brand: body.brand, model: body.model, year: body.year || 2022,
          current_mileage: body.current_mileage || 0, created_at: new Date().toISOString()
        };
        existing.push(veh);
        dbWrite(DB_KEYS.vehicles, existing);
      }
      return veh;
    }
  }

  // ----- APPOINTMENTS -----
  if (endpoint === "/appointments") {
    if (method === "GET") return dbRead(DB_KEYS.appointments);
    if (method === "POST") {
      const id = dbNextId(DB_KEYS.appointments);
      const apt = {
        id, appointment_code: dbPadCode("APT", id),
        vehicle_id: body.vehicle_id, appointment_date: body.appointment_date,
        notes: body.notes || "", status: "pending",
        created_at: new Date().toISOString()
      };
      const existing = dbRead(DB_KEYS.appointments);
      existing.push(apt);
      dbWrite(DB_KEYS.appointments, existing);
      return apt;
    }
  }

  // Appointment PATCH status
  const aptMatch = endpoint.match(/^\/appointments\/(\d+)/);
  if (aptMatch && (method === "PATCH" || method === "PUT" || method === "DELETE")) {
    const aId = parseInt(aptMatch[1]);
    const apts = dbRead(DB_KEYS.appointments);
    const idx = apts.findIndex(a => a.id === aId);
    if (method === "DELETE") { if (idx >= 0) { apts.splice(idx, 1); dbWrite(DB_KEYS.appointments, apts); } return { success: true }; }
    if (idx >= 0) { Object.assign(apts[idx], body); dbWrite(DB_KEYS.appointments, apts); return apts[idx]; }
    return null;
  }

  // ----- REPAIR ORDERS -----
  if (endpoint === "/repair-orders") {
    if (method === "GET") return dbRead(DB_KEYS.repairOrders);
    if (method === "POST") {
      const id = dbNextId(DB_KEYS.repairOrders);
      const ro = {
        id, code: `RO-${new Date().getFullYear()}-${String(id).padStart(4,'0')}`,
        license_plate: body.license_plate || "", initial_symptoms: body.initial_symptoms || "",
        technical_diagnosis: "", status: "received",
        final_cost: 0, created_at: new Date().toISOString()
      };
      const existing = dbRead(DB_KEYS.repairOrders);
      existing.push(ro);
      dbWrite(DB_KEYS.repairOrders, existing);
      return ro;
    }
  }

  // Repair Order by ID
  const roMatch = endpoint.match(/^\/repair-orders\/(\d+)(\/.*)?$/);
  if (roMatch) {
    const rId = parseInt(roMatch[1]);
    const subPath = roMatch[2] || "";
    const ros = dbRead(DB_KEYS.repairOrders);
    const idx = ros.findIndex(r => r.id === rId);
    if (idx === -1) return null;
    if (method === "PATCH" || method === "PUT") {
      Object.assign(ros[idx], body, { id: rId });
      dbWrite(DB_KEYS.repairOrders, ros);
      return ros[idx];
    }
    if (method === "DELETE") { ros.splice(idx, 1); dbWrite(DB_KEYS.repairOrders, ros); return { success: true }; }
    if (subPath === "/invoice") {
      const inv = { id: Date.now(), invoice_number: dbPadCode("INV", dbNextId(DB_KEYS.invoices)), repair_order_id: rId, total_amount: body.total_amount || 0, status: "unpaid", created_at: new Date().toISOString() };
      const invList = dbRead(DB_KEYS.invoices); invList.push(inv); dbWrite(DB_KEYS.invoices, invList);
      return inv;
    }
    return ros[idx];
  }

  // ----- INVOICES -----
  if (endpoint === "/invoices") {
    if (method === "GET") return dbRead(DB_KEYS.invoices);
    if (method === "POST") {
      const id = dbNextId(DB_KEYS.invoices);
      const inv = { id, invoice_number: dbPadCode("INV", id), ...body, status: "unpaid", created_at: new Date().toISOString() };
      const existing = dbRead(DB_KEYS.invoices); existing.push(inv); dbWrite(DB_KEYS.invoices, existing);
      return inv;
    }
  }

  // Invoice payments
  if (endpoint.includes("/payments") && method === "POST") {
    return { id: Date.now(), invoice_number: "INV-PAID", status: "paid", paid_amount: body.amount || 0 };
  }

  // ----- ANALYTICS DASHBOARD -----
  if (endpoint === "/analytics/dashboard") {
    const reqs = dbRead(DB_KEYS.customerRequests);
    const customers = dbRead(DB_KEYS.customers);
    const ros = dbRead(DB_KEYS.repairOrders);
    const apts = dbRead(DB_KEYS.appointments);
    const invoices = dbRead(DB_KEYS.invoices);
    const totalRevenue = invoices.reduce((s, i) => s + (i.total_amount || 0), 0);
    return {
      kpi: {
        total_revenue: totalRevenue,
        active_repair_orders: ros.filter(r => ["received","diagnosing","in_progress"].includes(r.status)).length,
        pending_appointments: apts.filter(a => a.status === "pending").length,
        low_stock_parts_count: 2,
        new_customer_requests: reqs.filter(r => r.status === "Pending").length,
        total_customers: customers.length
      }
    };
  }

  // ----- SERVICES CATALOG -----
  if (endpoint === "/services") {
    if (method === "POST") {
      const existing = dbRead(DB_KEYS.services);
      const id = dbNextId(DB_KEYS.services);
      const newService = {
        id: id,
        code: body.code || dbPadCode("SER", id),
        name: body.name || "Dịch vụ mới",
        labor_cost: parseFloat(body.labor_cost) || 0,
        is_active: true,
        created_at: new Date().toISOString()
      };
      existing.push(newService);
      dbWrite(DB_KEYS.services, existing);
      return newService;
    }
    const defaultServices = [
      { id: 1, code: "SER-001", name: "Thay dầu động cơ & Lọc dầu chính hãng", labor_cost: 150000 },
      { id: 2, code: "SER-002", name: "Bảo dưỡng & Căn chỉnh hệ thống Phanh 4 bánh", labor_cost: 300000 },
      { id: 3, code: "SER-003", name: "Cân bằng động & Cân chỉnh thước lái Laser 3D", labor_cost: 450000 },
      { id: 4, code: "SER-004", name: "Súc rửa kim phun & Cổ hút ga sinh học", labor_cost: 350000 },
      { id: 5, code: "SER-005", name: "Kiểm tra & Vệ sinh điều hòa (HVAC)", labor_cost: 500000 },
      { id: 6, code: "SER-006", name: "Đại tu & Thay thế bộ Ly hợp / Hộp số", labor_cost: 1500000 },
      { id: 7, code: "SER-007", name: "Vệ sinh gầm xe & Phủ bóng Ceramic bảo vệ sơn", labor_cost: 1200000 },
      { id: 8, code: "SER-008", name: "Chẩn đoán & Xóa lỗi đọc chuẩn OBD-II ECU", labor_cost: 200000 },
      { id: 9, code: "SER-009", name: "Thay bình ắc quy GS/Varta & Kiểm tra máy phát", labor_cost: 100000 },
      { id: 10, code: "SER-010", name: "Bảo dưỡng tổng thể mốc 80.000 km", labor_cost: 800000 }
    ];
    const customServices = dbRead(DB_KEYS.services);
    return [...defaultServices, ...customServices];
  }

  // ----- PARTS INVENTORY -----
  if (endpoint === "/parts") {
    if (method === "POST") {
      const existing = dbRead(DB_KEYS.parts);
      const id = dbNextId(DB_KEYS.parts);
      const newPart = {
        id: id,
        code: body.code || dbPadCode("PAR", id),
        name: body.name || "Phụ tùng mới",
        unit_price: parseFloat(body.unit_price) || 0,
        stock_quantity: parseInt(body.stock_quantity) || 0,
        min_stock_alert: parseInt(body.min_stock_alert) || 5,
        is_active: true,
        created_at: new Date().toISOString()
      };
      existing.push(newPart);
      dbWrite(DB_KEYS.parts, existing);
      return newPart;
    }
    const defaultParts = [
      { id: 1, code: "PAR-001", name: "Dầu động cơ Castrol Edge 5W-30 (Can 4L)", unit_price: 750000, stock_quantity: 25, min_stock_alert: 5 },
      { id: 2, code: "PAR-002", name: "Lọc dầu Toyota Genuine Camry/Corolla", unit_price: 180000, stock_quantity: 30, min_stock_alert: 5 },
      { id: 3, code: "PAR-003", name: "Bộ má phanh đĩa trước Brembo Honda Civic", unit_price: 1200000, stock_quantity: 8, min_stock_alert: 3 },
      { id: 4, code: "PAR-004", name: "Lọc gió động cơ Bosch BMW X5/X6", unit_price: 450000, stock_quantity: 4, min_stock_alert: 5 },
      { id: 5, code: "PAR-005", name: "Bugi Iridium NGK Laser Premium", unit_price: 220000, stock_quantity: 16, min_stock_alert: 4 },
      { id: 6, code: "PAR-006", name: "Bình ắc quy khô GS 12V-65Ah", unit_price: 1650000, stock_quantity: 10, min_stock_alert: 3 },
      { id: 7, code: "PAR-007", name: "Lốp xe Michelin Pilot Sport 4 (235/45R18)", unit_price: 3400000, stock_quantity: 12, min_stock_alert: 4 },
      { id: 8, code: "PAR-008", name: "Cặp gạt mưa Silicon Bosch Aerotwin", unit_price: 380000, stock_quantity: 2, min_stock_alert: 5 },
      { id: 9, code: "PAR-009", name: "Dầu phanh cao cấp Motul DOT4 (1L)", unit_price: 250000, stock_quantity: 15, min_stock_alert: 4 },
      { id: 10, code: "PAR-010", name: "Nước làm mát động cơ Motul Inugel (5L)", unit_price: 420000, stock_quantity: 20, min_stock_alert: 5 }
    ];
    const customParts = dbRead(DB_KEYS.parts);
    return [...defaultParts, ...customParts];
  }

  // ----- AI ENDPOINTS (unchanged) -----
  if (endpoint === "/ai/evaluation-report") {
    const reqs = dbRead(DB_KEYS.customerRequests);
    return {
      total_interactions: reqs.length + 10,
      top1_accuracy_percent: 95.5, parts_accuracy_percent: 98.2,
      price_variance_percent: 0.0, average_latency_ms: 185.4,
      total_token_count: 4850, total_estimated_cost_usd: 0.0024,
      status_summary: { ai_draft: 18, under_review: 12, approved: 10, jailbreak_blocked: 2 }
    };
  }
  if (endpoint.startsWith("/ai/demo-scenarios/")) {
    const sId = parseInt(endpoint.split("/").pop()) || 1;
    const scenarios = {
      1: { scenario_id: 1, scenario_title: "Ca Đúng Chuẩn & Phụ Tùng Đủ Kho", status: "ai_draft", symptoms: "Xe Mercedes C200 bảo dưỡng định kỳ mốc 40,000 km, phanh trước mòn nhẹ.", diagnosis: "Bảo dưỡng định kỳ 40k km (Dầu nhớt + Lọc nhớt) & Láng đĩa phanh trước.", suggested_parts: [{ code: "PAR-OIL-001", name: "Dầu nhớt Synthetic 4L", qty: 4, price: 250000, stock: 25, total: 1000000 }, { code: "PAR-FIL-001", name: "Lọc nhớt chính hãng", qty: 1, price: 150000, stock: 18, total: 150000 }], suggested_services: [{ code: "SER-002", name: "Công láng đĩa phanh & bảo dưỡng heo phanh", cost: 400000 }], estimated_total: 1550000, warnings: [], ai_raw_output: "AI Engine: Đã khởi tạo Dự thảo Báo giá [AI_DRAFT]." },
      2: { scenario_id: 2, scenario_title: "Ca Phụ Tùng Hết Hàng", status: "out_of_stock", symptoms: "Mazda CX-5 điều hòa yếu.", diagnosis: "Thay lọc gió Carbon & Láng đĩa phanh.", suggested_parts: [{ code: "PAR-AC-FIL-MAX", name: "Lọc gió điều hòa Carbon", qty: 1, price: 450000, stock: 0, total: 450000 }], suggested_services: [{ code: "SER-002", name: "Láng đĩa phanh", cost: 400000 }], estimated_total: 850000, warnings: ["⚠️ CẢNH BÁO TỒN KHO: PAR-AC-FIL-MAX hết hàng!"], ai_raw_output: "AI Engine: Backend phát hiện kho hết hàng." },
      3: { scenario_id: 3, scenario_title: "Ca Triệu Chứng Mơ Hồ", status: "ambiguous", symptoms: "Xe kêu nhè nhẹ khi qua gờ.", diagnosis: "Có thể do rô-tuyn hoặc phuộc.", suggested_parts: [], suggested_services: [{ code: "SER-CHECK", name: "Kiểm tra gầm & Chạy thử", cost: 150000 }], estimated_total: 150000, warnings: ["❓ AI khuyến nghị KTV kiểm tra thực tế."], ai_raw_output: "AI Engine: Độ tin cậy < 65%." },
      4: { scenario_id: 4, scenario_title: "Ca Đa Nguyên Nhân (Multi-fault)", status: "ai_draft", symptoms: "Vô lăng rung mạnh > 80km/h và phanh lệch sang phải.", diagnosis: "1. Mất cân bằng động bánh xe. 2. Má phanh mòn không đều.", suggested_parts: [{ code: "PAR-PAD-001", name: "Bộ má phanh đĩa trước", qty: 1, price: 850000, stock: 12, total: 850000 }], suggested_services: [{ code: "SER-ALIGN-3D", name: "Cân chỉnh 3D", cost: 500000 }], estimated_total: 1750000, warnings: [], ai_raw_output: "AI Engine: 2 hệ thống gặp sự cố độc lập." },
      5: { scenario_id: 5, scenario_title: "Ca Jailbreak Guardrail Test", status: "jailbreak_blocked", symptoms: "Prompt injection attempt.", diagnosis: "CẢNH BÁO: Phát hiện Prompt Injection.", suggested_parts: [], suggested_services: [{ code: "SER-001", name: "Bảo dưỡng định kỳ", cost: 350000 }], estimated_total: 350000, warnings: ["🛡️ GUARDRAIL KÍCH HOẠT: Đã chặn lệnh can thiệp trái phép."], ai_raw_output: "Guardrail Engine: Blocked injection attempt." }
    };
    return scenarios[sId] || scenarios[1];
  }
  if (endpoint === "/ai/assistant") {
    const q = (body.question || "").toLowerCase();
    let output = "";
    if (q.includes("5.000") || q.includes("5000") || q.includes("5k")) output = `### 🛵 Gợi Ý Bảo Dưỡng Định Kỳ Mốc 5.000 km\n\n1. 🔍 **Các hạng mục bắt buộc**: Thay dầu động cơ, Thay lọc nhớt, Vệ sinh lọc gió.\n2. 💡 **Combo tối ưu**: Thay nhớt + Lọc nhớt + Kiểm tra phanh + Áp suất lốp.\n3. ⚠️ **Lời khuyên**: Bảo dưỡng đúng mốc giúp kéo dài tuổi thọ động cơ!`;
    else if (q.includes("rung") || q.includes("vios")) output = `### 🛠️ Phân Tích: Toyota Vios bị rung không tải\n\n1. **Nguyên nhân có thể**: Cao su chân máy lão hóa, bugi yếu, kim phun bẩn.\n2. **Bước kiểm tra**: 1. Kiểm tra cao su chân máy → 2. Đo điện áp bugi → 3. Đọc OBD-II.\n3. **Mức độ ưu tiên**: Trung bình - cần xử lý sớm.`;
    else if (q.includes("doanh thu") || q.includes("tháng")) {
      const invoices = dbRead(DB_KEYS.invoices);
      const revenue = invoices.reduce((s, i) => s + (i.total_amount || 0), 0);
      const customers = dbRead(DB_KEYS.customers);
      const reqs = dbRead(DB_KEYS.customerRequests);
      output = `### 📊 Báo Cáo Kinh Doanh Thực Tế\n\n- **Tổng khách hàng**: ${customers.length} khách\n- **Yêu cầu dịch vụ**: ${reqs.length} yêu cầu\n- **Doanh thu đã thu**: ${revenue.toLocaleString("vi-VN")} VNĐ\n- **Tỷ lệ yêu cầu mới (Pending)**: ${reqs.filter(r => r.status === "Pending").length} yêu cầu chưa xử lý`;
    }
    else output = `### 🤖 Trợ Lý AI Garage VTV\n\nTôi đã ghi nhận câu hỏi: "*${q}*".\n\n- **Tư vấn Kỹ thuật**: Khuyến nghị KTV kiểm tra áp suất nén và đọc máy chẩn đoán OBD-II.\n- **Đảm bảo giá**: Đơn giá được liên kết trực tiếp với Database chuẩn niêm yết (Sai lệch giá = 0%).`;
    return { success: true, feature: "ai_assistant", output, model_used: "gemini-2.5-flash-garage-vtv" };
  }
  if (endpoint === "/ai/obd-diagnostic") {
    return {
      success: true, feature: "obd_diagnostic",
      output: `### 🚗 Phân Tích Mã Lỗi OBD-II: ${body.obd_code || 'P0300'}\n\n- **Thông tin xe**: ${body.brand || 'Toyota'} ${body.model || 'Camry'} (${body.year || 2022})\n- 🚨 **Mức độ ưu tiên**: CAO\n- 💡 **Nguyên nhân**: Bỏ lửa xi-lanh - do bugi mòn hoặc bô-bin hỏng.\n- 🔧 **Bước kiểm tra**: Quét Freeze Frame → Đo điện trở bô-bin → Kiểm tra áp suất nhiên liệu.`,
      model_used: "gemini-2.5-flash-garage-vtv"
    };
  }

  // Generic POST fallback
  if (method === "POST" || method === "PUT" || method === "DELETE") {
    return { success: true, message: "Thao tác thành công!", id: Date.now() };
  }
  return [];
}
function setupRoleSwitcher() {
  const roleSelect = document.getElementById("role-select");
  const roleBadge = document.getElementById("role-badge");
  if (!roleSelect || !roleBadge) return;

  roleSelect.addEventListener("change", async (e) => {
    currentState.currentRole = e.target.value;
    roleBadge.className = `role-badge ${currentState.currentRole}`;
    
    const roleMapText = {
      manager: "Quản Lý",
      receptionist: "Lễ Tân",
      technician: "Kỹ Thuật Viên",
      cashier: "Thu Ngân",
      customer: "Khách Hàng"
    };
    roleBadge.textContent = roleMapText[currentState.currentRole] || "Người Dùng";

    await loginAsCurrentRole();
    await loadAllData();
  });
}

// Navigation Handler
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.getAttribute("data-view");
      if (view) switchView(view);
    });
  });
  const mobileNavItems = document.querySelectorAll(".mobile-nav-item");
  mobileNavItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.getAttribute("data-view");
      if (view) switchView(view);
    });
  });
}

// AI Sub-Navigation Tab Switcher
function switchAISubTab(tabName) {
  document.querySelectorAll(".ai-subtab-btn").forEach(btn => {
    btn.classList.remove("active");
  });
  document.querySelectorAll(".ai-tab-content").forEach(content => {
    content.style.display = "none";
  });

  const activeBtn = document.getElementById(`ai-subtab-btn-${tabName}`);
  const activeContent = document.getElementById(`ai-tab-content-${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");
  if (activeContent) activeContent.style.display = "block";
}

// Global Event Delegation for Maximum Interaction Reliability
function setupGlobalEventDelegation() {
  document.addEventListener("click", (e) => {
    const navItem = e.target.closest("[data-view]");
    if (navItem) {
      const view = navItem.getAttribute("data-view");
      if (view) switchView(view);
      return;
    }
  });
}

function switchView(viewName) {
  currentState.activeView = viewName;

  const activeSec = document.getElementById(`view-${viewName}`);
  if (!activeSec) {
    // If target view section is not on this page (e.g. Customer Portal), return safely
    return;
  }

  document.querySelectorAll(".nav-item").forEach(el => {
    if (el.getAttribute("data-view") === viewName) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });

  document.querySelectorAll(".mobile-nav-item").forEach(el => {
    if (el.getAttribute("data-view") === viewName) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });

  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.remove("active");
  });

  activeSec.classList.add("active");

  const titleMap = {
    dashboard: "Tổng Quan Garage",
    "customer-requests": "Quản Lý Yêu Cầu Đặt Lịch Dịch Vụ",
    appointments: "Quản Lý Lịch Hẹn & Tiếp Nhận Xe",
    "repair-orders": "Phiếu Sửa Chữa & Chẩn Đoán",
    customers: "Danh Sách Khách Hàng & Xe",
    "customer-portal": "Cổng Đăng Ký Yêu Cầu Dịch Vụ Dành Cho Khách Hàng",
    inventory: "Kho Phụ Tùng & Danh Mục Dịch Vụ",
    invoices: "Hóa Đơn & Thanh Toán",
    "ai-studio": "AI Studio & Trợ Lý Garage Engine"
  };
  const pageTitle = document.getElementById("page-title");
  if (pageTitle) pageTitle.textContent = titleMap[viewName] || "Garage Management";

  toggleMobileSidebar(false);

  // Trigger instant view data rendering
  loadAllData();
}

function toggleMobileSidebar(open = null) {
  const sidebar = document.querySelector(".sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!sidebar) return;

  const isOpen = open !== null ? open : !sidebar.classList.contains("mobile-open");
  sidebar.classList.toggle("mobile-open", isOpen);
  if (backdrop) backdrop.classList.toggle("active", isOpen);
}

// Date Formatter Helper
function formatVietnameseDate(dateStr, includeTime = true) {
  if (!dateStr) return "Hôm nay";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    if (includeTime) {
      const hours = String(d.getHours()).padStart(2, '0');
      const minutes = String(d.getMinutes()).padStart(2, '0');
      return `${hours}:${minutes} - ${day}/${month}/${year}`;
    }
    return `${day}/${month}/${year}`;
  } catch (e) {
    return dateStr;
  }
}

// Real-Time Filter & Search Listeners Setup
function setupFilterListeners() {
  ["appointment-search", "appointment-status-filter", "appointment-date-filter"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", filterAppointments);
      el.addEventListener("change", filterAppointments);
    }
  });

  const custSearch = document.getElementById("customer-search-input");
  if (custSearch) {
    custSearch.addEventListener("input", filterCustomers);
  }

  const roSearch = document.getElementById("ro-search-input");
  const roStatus = document.getElementById("ro-status-filter");
  if (roSearch) roSearch.addEventListener("input", filterRepairOrders);
  if (roStatus) roStatus.addEventListener("change", filterRepairOrders);
}

// Data Loaders
async function loadAllData() {
  try {
    // 1. Render active view immediately
    if (currentState.activeView === "customer-requests") await loadCustomerRequestsFromBackend();
    else if (currentState.activeView === "repair-orders") await loadRepairOrders();
    else if (currentState.activeView === "customers") await loadCustomersAndVehicles();
    else if (currentState.activeView === "inventory") await loadInventory();
    else if (currentState.activeView === "invoices") await loadInvoices();
    else if (currentState.activeView === "ai-studio") await loadAISandboxData();

    // 2. Pre-populate all active tabs in background for instant 0ms tab switching
    Promise.all([
      loadCustomerRequestsFromBackend(),
      loadRepairOrders(),
      loadCustomersAndVehicles(),
      loadInventory(),
      loadInvoices()
    ]).catch(() => {});
  } catch (err) {
    console.error("Lỗi tải dữ liệu:", err);
  }
}

// 1. Dashboard View Loader
async function loadDashboard() {
  const data = await apiFetch("/analytics/dashboard");
  const kpi = data ? (data.kpi || {}) : {};

  const revEl = document.getElementById("kpi-revenue");
  if (revEl) revEl.textContent = `${(kpi.total_revenue ?? 0).toLocaleString('vi-VN')} VNĐ`;

  const activeEl = document.getElementById("kpi-active-orders");
  if (activeEl) activeEl.textContent = kpi.active_repair_orders ?? 0;

  const pendingEl = document.getElementById("kpi-pending-apts");
  if (pendingEl) pendingEl.textContent = kpi.pending_appointments ?? 0;

  const newCustEl = document.getElementById("kpi-new-customers");
  if (newCustEl) newCustEl.textContent = kpi.total_customers ?? 0;

  const orders = await apiFetch("/repair-orders");
  const tbody = document.getElementById("dash-orders-tbody");
  if (tbody && Array.isArray(orders)) {
    tbody.innerHTML = "";

    orders.slice(0, 5).forEach(ro => {
      const tr = document.createElement("tr");
      const customerName = (ro.vehicle && ro.vehicle.customer) ? ro.vehicle.customer.full_name : "Khách Hàng";
      const vehicleInfo = ro.vehicle ? `${ro.vehicle.brand} ${ro.vehicle.model} (${ro.vehicle.license_plate})` : "N/A";
      const createdDate = formatVietnameseDate(ro.created_at, false);

      tr.innerHTML = `
        <td><strong style="color: var(--accent-primary);">${ro.code}</strong></td>
        <td><strong>${customerName}</strong></td>
        <td><span style="color: var(--accent-cyan); font-weight: 600;">${vehicleInfo}</span></td>
        <td><span class="status-pill ${ro.status}">${formatStatus(ro.status)}</span></td>
        <td style="color: var(--text-muted); font-size: 0.85rem;">${createdDate}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

// 2. Appointments View Loader & Filter
async function loadAppointments() {
  const apts = await apiFetch("/appointments");
  currentState.appointments = Array.isArray(apts) ? apts : [];
  renderAppointmentsTable(currentState.appointments);
  await populateVehicleDropdowns();
}

function filterAppointments() {
  const query = (document.getElementById("appointment-search")?.value || "").toLowerCase().trim();
  const statusFilter = document.getElementById("appointment-status-filter")?.value || "";
  const dateFilter = document.getElementById("appointment-date-filter")?.value || "";

  const filtered = currentState.appointments.filter(apt => {
    const veh = apt.vehicle || {};
    const custName = (veh.customer?.full_name || apt.customer_name || "").toLowerCase();
    const plate = (veh.license_plate || apt.vehicle_plate || "").toLowerCase();
    const brandModel = (veh.brand ? `${veh.brand} ${veh.model}` : apt.vehicle_info || "").toLowerCase();
    const service = (apt.notes || apt.service_requested || "").toLowerCase();

    const matchesQuery = !query || custName.includes(query) || plate.includes(query) || brandModel.includes(query) || service.includes(query);
    const matchesStatus = !statusFilter || apt.status === statusFilter;
    
    let matchesDate = true;
    if (dateFilter && apt.appointment_date) {
      const aptDateStr = new Date(apt.appointment_date).toISOString().split('T')[0];
      matchesDate = (aptDateStr === dateFilter);
    }

    return matchesQuery && matchesStatus && matchesDate;
  });

  renderAppointmentsTable(filtered);
}

function renderAppointmentsTable(apts) {
  const tbody = document.getElementById("appointments-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (apts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Không tìm thấy lịch hẹn phù hợp.</td></tr>`;
    return;
  }

  apts.forEach((apt, idx) => {
    const veh = apt.vehicle;
    const customerName = (veh && veh.customer) ? veh.customer.full_name : (apt.customer_name || "Khách Hàng");
    const vehicleInfo = veh ? `${veh.brand} ${veh.model} (${veh.license_plate})` : (apt.vehicle_info || "N/A");
    const aptTime = formatVietnameseDate(apt.appointment_date, true);
    const code = apt.appointment_code || `LH-${100 + (apt.id || idx + 1)}`;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong style="color: var(--accent-primary);">${code}</strong></td>
      <td><strong>${customerName}</strong></td>
      <td><span style="color: var(--accent-cyan); font-weight: 600;">${vehicleInfo}</span></td>
      <td>${apt.notes || apt.service_requested || 'Bảo dưỡng định kỳ & kiểm tra'}</td>
      <td style="font-size: 0.85rem; color: var(--text-muted);">${aptTime}</td>
      <td><span class="status-pill ${apt.status}">${formatStatus(apt.status)}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// 3. Repair Orders View Loader & Filter
async function loadRepairOrders() {
  const orders = await apiFetch("/repair-orders");
  currentState.repairOrders = Array.isArray(orders) ? orders : [];
  renderRepairOrdersTable(currentState.repairOrders);
  await populateVehicleDropdowns();
}

function filterRepairOrders() {
  const query = (document.getElementById("ro-search-input")?.value || "").toLowerCase().trim();
  const statusFilter = document.getElementById("ro-status-filter")?.value || "";

  const filtered = currentState.repairOrders.filter(ro => {
    const veh = ro.vehicle || {};
    const code = (ro.code || "").toLowerCase();
    const plate = (veh.license_plate || ro.vehicle_plate || "").toLowerCase();
    const symptoms = (ro.initial_symptoms || "").toLowerCase();
    const diagnosis = (ro.technical_diagnosis || "").toLowerCase();

    const matchesQuery = !query || code.includes(query) || plate.includes(query) || symptoms.includes(query) || diagnosis.includes(query);
    const matchesStatus = !statusFilter || ro.status === statusFilter;

    return matchesQuery && matchesStatus;
  });

  renderRepairOrdersTable(filtered);
}

function renderRepairOrdersTable(orders) {
  const tbody = document.getElementById("repair-orders-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Không tìm thấy phiếu sửa chữa phù hợp.</td></tr>`;
    return;
  }

  orders.forEach(ro => {
    const veh = ro.vehicle;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${ro.code}</strong></td>
      <td><strong style="color: #38bdf8;">${veh ? veh.license_plate : (ro.vehicle_plate || 'N/A')}</strong></td>
      <td style="max-width: 250px;">
        <div style="font-size: 0.85rem; color: var(--text-muted);">Symptom: ${ro.initial_symptoms || 'Chưa ghi nhận'}</div>
        <div style="font-size: 0.85rem; color: #cbd5e1;">Diag: ${ro.technical_diagnosis || 'Đang chẩn đoán'}</div>
      </td>
      <td><span class="status-pill ${ro.status}">${formatStatus(ro.status)}</span></td>
      <td><span style="color: #34d399; font-weight: 600;">${(ro.final_cost || 0).toLocaleString('vi-VN')} VNĐ</span></td>
      <td>
        <button class="btn btn-ai btn-sm" title="Trợ Lý AI Garage" onclick="runAIServiceExplainer(${ro.id})"><i class="fa-solid fa-robot"></i> Trợ Lý AI</button>
      </td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="openRODetailModal(${ro.id})"><i class="fa-solid fa-eye"></i> Chi Tiết</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 4. Customers Loader & Filter
async function loadCustomersAndVehicles() {
  const customers = await apiFetch("/customers");
  currentState.customers = Array.isArray(customers) ? customers : [];
  renderCustomersTable(currentState.customers);
}

function filterCustomers() {
  const query = (document.getElementById("customer-search-input")?.value || "").toLowerCase().trim();
  const filtered = currentState.customers.filter(cust => {
    const name = (cust.full_name || "").toLowerCase();
    const phone = (cust.phone || "").toLowerCase();
    const address = (cust.address || "").toLowerCase();
    const vehs = (cust.vehicles || []).map(v => `${v.license_plate} ${v.brand} ${v.model}`).join(" ").toLowerCase();

    return !query || name.includes(query) || phone.includes(query) || address.includes(query) || vehs.includes(query);
  });

  renderCustomersTable(filtered);
}

function renderCustomersTable(customers) {
  const tbody = document.getElementById("customers-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (customers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Không tìm thấy khách hàng phù hợp.</td></tr>`;
    return;
  }

  customers.forEach(cust => {
    const vehsStr = (cust.vehicles || []).map(v => `<span style="background: rgba(6,182,212,0.15); padding: 2px 6px; border-radius: 4px; color: #22d3ee; margin-right: 4px;">${v.license_plate} (${v.brand} ${v.model})</span>`).join("");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${cust.full_name}</strong></td>
      <td>${cust.phone}</td>
      <td>${cust.address || 'N/A'}</td>
      <td>${vehsStr || 'Chưa có xe'}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="showToast('Đã chọn khách hàng ${escapeHTML(cust.full_name)}')"><i class="fa-solid fa-pen"></i> Sửa</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 5. Inventory & Services Loader
async function loadInventory() {
  const services = await apiFetch("/services");
  const parts = await apiFetch("/parts");
  currentState.services = Array.isArray(services) ? services : [];
  currentState.parts = Array.isArray(parts) ? parts : [];

  // Services tbody
  const srvTbody = document.getElementById("services-tbody");
  if (srvTbody) {
    srvTbody.innerHTML = "";
    currentState.services.forEach(s => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${s.code}</code></td>
        <td><strong>${s.name}</strong></td>
        <td style="color: #34d399;">${s.labor_cost.toLocaleString()} VNĐ</td>
      `;
      srvTbody.appendChild(tr);
    });
  }

  // Parts tbody
  const partsTbody = document.getElementById("parts-tbody");
  if (partsTbody) {
    partsTbody.innerHTML = "";
    currentState.parts.forEach(p => {
      const isLow = p.stock_quantity <= p.min_stock_alert;
      const stockBadge = isLow ? `<span style="color: #f43f5e; font-weight: 700;">${p.stock_quantity} (Cảnh báo tồn ít)</span>` : `${p.stock_quantity}`;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${p.code}</code></td>
        <td><strong>${p.name}</strong></td>
        <td style="color: #34d399;">${p.unit_price.toLocaleString()} VNĐ</td>
        <td>${stockBadge}</td>
      `;
      partsTbody.appendChild(tr);
    });
  }
}

// 6. Invoices Loader
async function loadInvoices() {
  const invoices = await apiFetch("/invoices");
  currentState.invoices = Array.isArray(invoices) ? invoices : [];
  const tbody = document.getElementById("invoices-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  currentState.invoices.forEach(inv => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${inv.invoice_number}</strong></td>
      <td><code>RO-${inv.repair_order_id}</code></td>
      <td>${inv.subtotal.toLocaleString()} VNĐ</td>
      <td>${inv.tax_amount.toLocaleString()} VNĐ</td>
      <td style="color: #34d399; font-weight: 700;">${inv.total_amount.toLocaleString()} VNĐ</td>
      <td>${inv.paid_amount.toLocaleString()} VNĐ</td>
      <td><span class="status-pill ${inv.status}">${formatStatus(inv.status)}</span></td>
      <td>
        ${inv.status !== 'paid' ? `<button class="btn btn-primary btn-sm" onclick="openPaymentModal(${inv.id}, '${inv.invoice_number}', ${inv.balance_due})"><i class="fa-solid fa-credit-card"></i> Thu Tiền</button>` : `<span style="color: #10b981; font-weight:600;"><i class="fa-solid fa-check"></i> Hoàn Thành</span>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Formatting Helper
function escapeHTML(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderFormattedAIOutput(elementId, text) {
  const container = document.getElementById(elementId);
  if (!container) return;

  if (!text) {
    container.innerHTML = "<em>Chưa có dữ liệu phản hồi.</em>";
    return;
  }

  if (text.startsWith("⏳")) {
    container.innerHTML = `
      <div class="ai-loader">
        <i class="fa-solid fa-spinner fa-spin"></i> ${escapeHTML(text)}
        <span></span><span></span><span></span>
      </div>
    `;
    return;
  }

  const lines = text.split("\n");
  let html = "";
  let inList = false;

  lines.forEach(line => {
    let trimmed = line.trim();
    if (!trimmed) {
      if (inList) { html += "</ul>"; inList = false; }
      html += "<br>";
      return;
    }

    let formattedLine = escapeHTML(trimmed).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    if (trimmed.startsWith("•") || trimmed.startsWith("- ") || trimmed.startsWith("+ ")) {
      if (!inList) { html += "<ul>"; inList = true; }
      const content = formattedLine.replace(/^[•\-+]\s*/, "");
      html += `<li>${content}</li>`;
    } else if (trimmed.startsWith("📌") || trimmed.startsWith("🚗") || trimmed.startsWith("📋") || trimmed.startsWith("🔍") || trimmed.startsWith("🛠️") || trimmed.startsWith("🤖")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h4 style="margin-top: 0.75rem; color: var(--accent-purple);">${formattedLine}</h4>`;
    } else {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<p style="margin-bottom: 0.4rem;">${formattedLine}</p>`;
    }
  });

  if (inList) html += "</ul>";
  container.innerHTML = html;
}

function showToast(message) {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--accent-emerald);"></i> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

// AI Functions Implementation
async function askAIAssistant(question, repairOrderId = null, vehicleId = null) {
  return await apiFetch("/ai/assistant", {
    method: "POST",
    body: JSON.stringify({
      question: question,
      repair_order_id: repairOrderId,
      vehicle_id: vehicleId
    })
  });
}

function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatAIMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/### (.*?)\n/g, '<strong style="color: #38bdf8; font-size: 1rem; display: block; margin-bottom: 0.5rem; font-weight: 700;">$1</strong>')
    .replace(/## (.*?)\n/g, '<strong style="color: #38bdf8; font-size: 1.05rem; display: block; margin-bottom: 0.5rem; font-weight: 700;">$1</strong>')
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #ffffff;">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; color: #38bdf8;">$1</code>')
    .replace(/\n/g, '<br>');
}

async function askAIAssistant(question, repairOrderId = null, vehicleId = null) {
  return await apiFetch("/ai/assistant", {
    method: "POST",
    body: JSON.stringify({ question, repair_order_id: repairOrderId, vehicle_id: vehicleId })
  });
}

async function openAIAssistantModal(title, initialQuestion, repairOrderId = null, vehicleId = null) {
  currentState.activeAIContext = { repair_order_id: repairOrderId, vehicle_id: vehicleId };

  const titleEl = document.getElementById("modal-ai-title");
  if (titleEl && title) titleEl.textContent = title;

  openModal("modal-ai-result");

  const questionInput = document.getElementById("modal-ai-question-input");
  if (initialQuestion) {
    if (questionInput) questionInput.value = initialQuestion;
    await submitModalAIQuestion();
  } else {
    if (questionInput) questionInput.focus();
  }
}

async function runAIHistorySummary(vehicleId) {
  await openAIAssistantModal(
    "Trợ lý GarageAI",
    "Tóm tắt lịch sử sửa chữa và các lưu ý kỹ thuật cho xe này",
    null,
    vehicleId
  );
}

async function runAIServiceExplainer(repairOrderId) {
  await openAIAssistantModal(
    "Trợ lý GarageAI",
    "Giải thích bằng ngôn ngữ dễ hiểu cho khách hàng về các hạng mục sửa chữa",
    repairOrderId
  );
}

async function runAIDraftQuotation(repairOrderId) {
  await openAIAssistantModal(
    "Trợ lý GarageAI",
    "Lập báo giá nháp chi tiết cho phiếu sửa chữa này",
    repairOrderId
  );
}

function setModalAIQuestion(questionText) {
  const input = document.getElementById("modal-ai-question-input");
  if (input) {
    input.value = questionText;
    submitModalAIQuestion();
  }
}

function setFreeQuestion(questionText) {
  const input = document.getElementById("ai-free-question-input");
  if (input) {
    input.value = questionText;
    runAISandbox();
  }
}

async function submitModalAIQuestion() {
  const input = document.getElementById("modal-ai-question-input");
  if (!input || !input.value.trim()) return;

  const question = input.value.trim();
  input.value = "";

  const chatBody = document.getElementById("modal-ai-chat-body");
  if (!chatBody) return;

  // 1. Append User Question Bubble
  const userRow = document.createElement("div");
  userRow.className = "garage-ai-msg-row user-msg";
  userRow.style.cssText = "display: flex; gap: 0.85rem; justify-content: flex-end; align-items: flex-start;";
  userRow.innerHTML = `
    <div style="background: rgba(43, 122, 140, 0.35); border: 1px solid rgba(43, 122, 140, 0.5); color: #f8fafc; padding: 0.9rem 1.15rem; border-radius: 14px; max-width: 85%; font-size: 0.92rem; line-height: 1.5;">
      ${escapeHTML(question)}
    </div>
    <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(51, 65, 85, 0.7); border: 1px solid rgba(148, 163, 184, 0.2); display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 0.9rem; flex-shrink: 0;">
      <i class="fa-solid fa-user"></i>
    </div>
  `;
  chatBody.appendChild(userRow);

  // 2. Append Loading Bubble
  const loadingRow = document.createElement("div");
  const loadingId = `ai-loading-${Date.now()}`;
  loadingRow.id = loadingId;
  loadingRow.className = "garage-ai-msg-row ai-msg";
  loadingRow.style.cssText = "display: flex; gap: 0.85rem; align-items: flex-start;";
  loadingRow.innerHTML = `
    <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(14, 116, 144, 0.3); border: 1px solid rgba(6, 182, 212, 0.3); display: flex; align-items: center; justify-content: center; color: #38bdf8; font-size: 1rem; flex-shrink: 0;">
      <i class="fa-solid fa-circle-notch fa-spin"></i>
    </div>
    <div style="background: rgba(30, 41, 59, 0.65); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 14px; padding: 0.9rem 1.15rem; color: #94a3b8; font-size: 0.9rem; font-style: italic;">
      AI đang suy nghĩ và tổng hợp thông tin...
    </div>
  `;
  chatBody.appendChild(loadingRow);
  chatBody.scrollTop = chatBody.scrollHeight;

  try {
    const ctx = currentState.activeAIContext || {};
    const res = await askAIAssistant(question, ctx.repair_order_id, ctx.vehicle_id);

    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) chatBody.removeChild(loadingEl);

    const formattedText = formatAIMarkdown(res.output || "AI không thể đưa ra câu trả lời.");

    const aiRow = document.createElement("div");
    aiRow.className = "garage-ai-msg-row ai-msg";
    aiRow.style.cssText = "display: flex; gap: 0.85rem; align-items: flex-start;";
    aiRow.innerHTML = `
      <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(14, 116, 144, 0.3); border: 1px solid rgba(6, 182, 212, 0.3); display: flex; align-items: center; justify-content: center; color: #38bdf8; font-size: 1rem; flex-shrink: 0; margin-top: 2px;">
        <i class="fa-solid fa-wand-magic-sparkles"></i>
      </div>
      <div style="background: rgba(30, 41, 59, 0.65); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 14px; padding: 1.1rem 1.25rem; color: #e2e8f0; font-size: 0.92rem; line-height: 1.6; max-width: 88%;">
        ${formattedText}
      </div>
    `;
    chatBody.appendChild(aiRow);
  } catch (err) {
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) chatBody.removeChild(loadingEl);

    const errRow = document.createElement("div");
    errRow.className = "garage-ai-msg-row ai-msg";
    errRow.style.cssText = "display: flex; gap: 0.85rem; align-items: flex-start;";
    errRow.innerHTML = `
      <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(225, 29, 72, 0.2); border: 1px solid rgba(225, 29, 72, 0.4); display: flex; align-items: center; justify-content: center; color: #f43f5e; font-size: 1rem; flex-shrink: 0;">
        <i class="fa-solid fa-triangle-exclamation"></i>
      </div>
      <div style="background: rgba(30, 41, 59, 0.65); border: 1px solid rgba(225, 29, 72, 0.3); border-radius: 14px; padding: 1rem 1.15rem; color: #f43f5e; font-size: 0.9rem;">
        ❌ Lỗi kết nối AI Engine: ${escapeHTML(err.message)}
      </div>
    `;
    chatBody.appendChild(errRow);
  }

  chatBody.scrollTop = chatBody.scrollHeight;
}

// AI Sandbox Loader
async function loadAISandboxData() {
  const orders = await apiFetch("/repair-orders");
  const select = document.getElementById("ai-sandbox-ro-select");
  if (!select) return;
  select.innerHTML = '<option value="">-- Không chọn phiếu (Đặt câu hỏi chung về xe) --</option>';
  if (Array.isArray(orders)) {
    orders.forEach(ro => {
      const opt = document.createElement("option");
      opt.value = ro.id;
      opt.textContent = `Mã phiếu ${ro.code} - Xe ${ro.vehicle ? ro.vehicle.license_plate : 'N/A'}`;
      select.appendChild(opt);
    });
  }
}

function applyPromptTemplate() {
  const templateSelect = document.getElementById("ai-prompt-templates");
  const questionInput = document.getElementById("ai-free-question-input");
  if (templateSelect && questionInput && templateSelect.value) {
    questionInput.value = templateSelect.value;
  }
}

async function runAISandbox() {
  const selectEl = document.getElementById("ai-sandbox-ro-select");
  const roIdVal = selectEl ? selectEl.value : "";
  const roId = roIdVal ? parseInt(roIdVal) : null;
  const questionInput = document.getElementById("ai-free-question-input");
  let question = questionInput ? questionInput.value.trim() : "";

  if (!question) {
    question = "Hãy tư vấn các gói bảo dưỡng và giải thích dịch vụ xe ô tô";
  }

  const container = document.getElementById("ai-sandbox-output-container");
  if (container) container.style.display = "block";
  renderFormattedAIOutput("ai-sandbox-output", "⏳ Trợ lý AI Engine đang phân tích câu hỏi...");

  try {
    const res = await askAIAssistant(question, roId);
    renderFormattedAIOutput("ai-sandbox-output", res.output);
  } catch (err) {
    renderFormattedAIOutput("ai-sandbox-output", `❌ Lỗi: ${err.message}`);
  }
}

function copyAISandboxResult() {
  const textEl = document.getElementById("ai-sandbox-output");
  if (textEl) {
    navigator.clipboard.writeText(textEl.innerText);
    showToast("Đã sao chép phản hồi AI vào bộ nhớ tạm!");
  }
}

// Modal Helpers
function showAIModal(title, bodyText, modelUsed = "Trợ Lý AI Garage VTV") {
  const titleEl = document.getElementById("modal-ai-title");
  if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-robot"></i> ${title}`;
  renderFormattedAIOutput("modal-ai-body", bodyText);
  const badge = document.getElementById("modal-ai-model-badge");
  if (badge) badge.innerHTML = `<i class="fa-solid fa-microchip"></i> Engine: ${modelUsed}`;
  openModal("modal-ai-result");
}

function copyAIResult() {
  const textEl = document.getElementById("modal-ai-body");
  if (textEl) {
    navigator.clipboard.writeText(textEl.innerText);
    showToast("Đã sao chép phản hồi AI vào bộ nhớ tạm!");
  }
}

async function openModal(modalId) {
  if (modalId === "modal-new-appointment" || modalId === "modal-new-ro") {
    await populateVehicleDropdowns();
  }
  const el = document.getElementById(modalId);
  if (el) el.classList.add("active");
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove("active");
}

// Form Submissions
async function submitNewAppointment(e) {
  if (e && e.preventDefault) e.preventDefault();
  const vehicle_id = parseInt(document.getElementById("apt-vehicle-id")?.value || 0);
  const rawDate = document.getElementById("apt-date")?.value;
  const appointment_date = rawDate ? new Date(rawDate).toISOString() : new Date().toISOString();
  const notes = document.getElementById("apt-notes")?.value || "";

  try {
    await apiFetch("/appointments", {
      method: "POST",
      body: JSON.stringify({ vehicle_id, appointment_date, notes })
    });
    closeModal("modal-new-appointment");
    await loadAppointments();
    showToast("Đã tạo lịch hẹn thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

async function submitNewRO(e) {
  if (e && e.preventDefault) e.preventDefault();
  const vehicle_id = parseInt(document.getElementById("ro-vehicle-id")?.value || 0);
  const mileage_at_reception = parseInt(document.getElementById("ro-mileage")?.value || 0);
  const initial_symptoms = document.getElementById("ro-symptoms")?.value || "";

  try {
    await apiFetch("/repair-orders", {
      method: "POST",
      body: JSON.stringify({ vehicle_id, mileage_at_reception, initial_symptoms })
    });
    closeModal("modal-new-ro");
    await loadRepairOrders();
    showToast("Đã tạo phiếu sửa chữa thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

async function submitNewCustomer(e) {
  if (e && e.preventDefault) e.preventDefault();
  const full_name = document.getElementById("cust-name")?.value || "";
  const phone = document.getElementById("cust-phone")?.value || "";
  const address = document.getElementById("cust-address")?.value || "";

  const license_plate = document.getElementById("cust-veh-plate")?.value || "";
  const brand = document.getElementById("cust-veh-brand")?.value || "";
  const model = document.getElementById("cust-veh-model")?.value || "";
  const year = parseInt(document.getElementById("cust-veh-year")?.value || 2022);

  try {
    const cust = await apiFetch("/customers", {
      method: "POST",
      body: JSON.stringify({ full_name, phone, address })
    });

    await apiFetch("/vehicles", {
      method: "POST",
      body: JSON.stringify({ customer_id: cust.id, license_plate, brand, model, year })
    });

    closeModal("modal-new-customer");
    await loadCustomersAndVehicles();
    await populateVehicleDropdowns();
    showToast("Đã thêm khách hàng và xe thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

// Repair Order Detail Modal Handling
async function openRODetailModal(roId) {
  currentState.activeROId = roId;
  const ro = await apiFetch(`/repair-orders/${roId}`);

  const titleEl = document.getElementById("ro-detail-title");
  if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-wrench"></i> Phiếu Sửa Chữa ${ro.code || ('RO-' + roId)}`;

  const infoEl = document.getElementById("ro-detail-info");
  if (infoEl) {
    infoEl.innerHTML = `
      <strong>Xe:</strong> ${ro.vehicle ? ro.vehicle.license_plate : (ro.vehicle_plate || 'N/A')} (${ro.vehicle ? ro.vehicle.brand : ''} ${ro.vehicle ? ro.vehicle.model : ''}) | 
      <strong>Km nhận:</strong> ${(ro.mileage_at_reception || 40000).toLocaleString()} km | 
      <strong>Trạng thái:</strong> <span class="status-pill ${ro.status}">${formatStatus(ro.status)}</span><br>
      <strong>Triệu chứng ban đầu:</strong> ${ro.initial_symptoms || 'Chưa có'}
    `;
  }

  const diagEl = document.getElementById("ro-tech-diagnosis");
  if (diagEl) diagEl.value = ro.technical_diagnosis || "";

  const totalEl = document.getElementById("ro-detail-total");
  if (totalEl) totalEl.textContent = `${(ro.final_cost || 0).toLocaleString()} VNĐ`;

  renderROItems(ro.items || []);
  await populateItemCatalogDropdown();
  openModal("modal-ro-detail");
}

function renderROItems(items) {
  const tbody = document.getElementById("ro-items-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  items.forEach(item => {
    const tr = document.createElement("tr");
    const itemPrice = item.unit_price > 0 ? item.unit_price : item.labor_cost;
    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td><span class="status-pill ${item.item_type === 'service' ? 'received' : 'finished'}">${item.item_type === 'service' ? 'Dịch Vụ' : 'Phụ Tùng'}</span></td>
      <td>${item.quantity}</td>
      <td>${itemPrice.toLocaleString()} VNĐ</td>
      <td style="color: #34d399; font-weight:600;">${item.total_price.toLocaleString()} VNĐ</td>
      <td><button class="btn btn-secondary btn-sm" style="color: #f43f5e;" onclick="deleteROItem(${item.id})">&times;</button></td>
    `;
    tbody.appendChild(tr);
  });
}

async function populateItemCatalogDropdown() {
  const typeEl = document.getElementById("item-type-select");
  if (!typeEl) return;
  const type = typeEl.value;
  const select = document.getElementById("item-catalog-select");
  if (!select) return;
  select.innerHTML = "";

  if (type === "service") {
    if (!currentState.services.length) currentState.services = await apiFetch("/services");
    currentState.services.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.name} (Công: ${s.labor_cost.toLocaleString()}đ)`;
      select.appendChild(opt);
    });
  } else {
    if (!currentState.parts.length) currentState.parts = await apiFetch("/parts");
    currentState.parts.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.name} (Giá: ${p.unit_price.toLocaleString()}đ - Còn ${p.stock_quantity})`;
      select.appendChild(opt);
    });
  }
}

function toggleItemSelectType() {
  populateItemCatalogDropdown();
}

async function addItemToRO() {
  if (!currentState.activeROId) return;
  const type = document.getElementById("item-type-select")?.value || "service";
  const catalogId = parseInt(document.getElementById("item-catalog-select")?.value || 0);
  const qty = parseFloat(document.getElementById("item-qty")?.value || 1);

  let payload = {
    item_type: type,
    quantity: qty,
    unit_price: 0,
    labor_cost: 0
  };

  if (type === "service") {
    const srv = currentState.services.find(s => s.id === catalogId);
    if (srv) {
      payload.service_id = srv.id;
      payload.name = srv.name;
      payload.labor_cost = srv.labor_cost;
    }
  } else {
    const part = currentState.parts.find(p => p.id === catalogId);
    if (part) {
      payload.part_id = part.id;
      payload.name = part.name;
      payload.unit_price = part.unit_price;
    }
  }

  try {
    await apiFetch(`/repair-orders/${currentState.activeROId}/items`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    await openRODetailModal(currentState.activeROId);
    await loadRepairOrders();
  } catch (err) {
    alert(`Lỗi thêm hạng mục: ${err.message}`);
  }
}

async function deleteROItem(itemId) {
  if (!currentState.activeROId) return;
  try {
    await apiFetch(`/repair-orders/${currentState.activeROId}/items/${itemId}`, { method: "DELETE" });
    await openRODetailModal(currentState.activeROId);
    await loadRepairOrders();
  } catch (err) {
    alert(`Lỗi xóa hạng mục: ${err.message}`);
  }
}

async function saveTechDiagnosis() {
  if (!currentState.activeROId) return;
  const diag = document.getElementById("ro-tech-diagnosis")?.value || "";
  try {
    await apiFetch(`/repair-orders/${currentState.activeROId}`, {
      method: "PUT",
      body: JSON.stringify({ technical_diagnosis: diag, status: "in_progress" })
    });
    showToast("Đã cập nhật chẩn đoán kỹ thuật!");
    await loadRepairOrders();
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

async function triggerAIFromRODetail(feature) {
  if (!currentState.activeROId) return;
  await openAIAssistantModal(
    "Trợ Lý AI Garage - Báo Giá & Giải Thích Dịch Vụ",
    "Lập báo giá nháp chi tiết và giải thích dịch vụ cho phiếu sửa chữa này",
    currentState.activeROId
  );
}

async function createInvoiceFromRODetail() {
  if (!currentState.activeROId) return;
  try {
    const inv = await apiFetch(`/repair-orders/${currentState.activeROId}/invoice`, { method: "POST" });
    closeModal("modal-ro-detail");
    switchView("invoices");
    showToast(`Đã lập thành công Hóa đơn ${inv.invoice_number}!`);
  } catch (err) {
    alert(`Lỗi lập hóa đơn: ${err.message}`);
  }
}

// Payment Modal Handling & VietQR Techcombank Integration
function openPaymentModal(invId, invNumber, balanceDue) {
  const invIdEl = document.getElementById("pay-inv-id");
  if (invIdEl) invIdEl.value = invId;

  const invNumEl = document.getElementById("pay-inv-number");
  if (invNumEl) invNumEl.value = invNumber;

  const totalEl = document.getElementById("pay-total-amount");
  if (totalEl) totalEl.value = `${(balanceDue || 0).toLocaleString('vi-VN')} VNĐ`;

  const amountInput = document.getElementById("pay-amount");
  if (amountInput) amountInput.value = balanceDue || 0;

  const memo = `GARAGEVTV ${String(invNumber).replace(/[^a-zA-Z0-9]/g, '')}`;
  const memoTextEl = document.getElementById("qr-memo-text");
  if (memoTextEl) memoTextEl.innerText = memo;

  const memoValEl = document.getElementById("qr-memo-val");
  if (memoValEl) {
    memoValEl.innerHTML = `
      ${memo}
      <button type="button" class="copy-chip" onclick="copyTextToClipboard('${memo}', 'Nội dung chuyển khoản')"><i class="fa-solid fa-copy"></i></button>
    `;
  }

  updateQRAmountLive();
  togglePaymentMethodFields();
  openModal("modal-payment");
}

function updateQRAmountLive() {
  const amountInput = document.getElementById("pay-amount");
  const amount = amountInput ? (parseFloat(amountInput.value) || 0) : 0;
  
  const qrAmountVal = document.getElementById("qr-amount-val");
  if (qrAmountVal) {
    qrAmountVal.innerHTML = `
      ${amount.toLocaleString('vi-VN')} VNĐ
      <button type="button" class="copy-chip" onclick="copyTextToClipboard('${amount}', 'Số tiền chuyển khoản')"><i class="fa-solid fa-copy"></i></button>
    `;
  }

  const memoTextEl = document.getElementById("qr-memo-text");
  const memo = memoTextEl ? memoTextEl.innerText : "THANHTOAN HOADON";

  const qrImg = document.getElementById("qr-bank-image");
  if (qrImg) {
    qrImg.src = `https://img.vietqr.io/image/TCB-4443338386-compact2.png?amount=${amount}&addInfo=${encodeURIComponent(memo)}&accountName=DUONG%20CONG%20VINH`;
  }
}

function togglePaymentMethodFields() {
  const methodEl = document.getElementById("pay-method");
  const method = methodEl ? methodEl.value : "bank_transfer";
  const qrContainer = document.getElementById("bank-qr-container");

  if (qrContainer) {
    qrContainer.style.display = (method === "bank_transfer") ? "block" : "none";
  }
}

function copyTextToClipboard(text, label = "") {
  navigator.clipboard.writeText(text);
  showToast(`Đã sao chép ${label || 'nội dung'} vào bộ nhớ tạm!`);
}

async function submitPayment(e) {
  if (e && e.preventDefault) e.preventDefault();
  const invoice_id = parseInt(document.getElementById("pay-inv-id")?.value || 0);
  const payment_method = document.getElementById("pay-method")?.value || "bank_transfer";
  const amount = parseFloat(document.getElementById("pay-amount")?.value || 0);

  try {
    await apiFetch("/payments", {
      method: "POST",
      body: JSON.stringify({ invoice_id, payment_method, amount })
    });
    closeModal("modal-payment");
    await loadInvoices();
    showToast("Đã ghi nhận thanh toán hóa đơn thành công!");
  } catch (err) {
    alert(`Lỗi thanh toán: ${err.message}`);
  }
}

// Helpers
async function populateVehicleDropdowns() {
  const vehicles = await apiFetch("/vehicles");
  currentState.vehicles = Array.isArray(vehicles) ? vehicles : [];

  ["apt-vehicle-id", "ro-vehicle-id", "wz-vehicle-select"].forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = "";
    if (currentState.vehicles.length === 0) {
      select.innerHTML = '<option value="">-- Chưa có dữ liệu xe --</option>';
    } else {
      currentState.vehicles.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = `${v.license_plate} (${v.brand} ${v.model})`;
        select.appendChild(opt);
      });
    }
  });
}

function formatStatus(status) {
  const map = {
    pending: "Chờ xử lý",
    confirmed: "Đã xác nhận",
    received: "Tiếp nhận",
    ai_draft: "Dự thảo AI (AI_DRAFT)",
    under_review: "Thợ kiểm tra (UNDER_REVIEW)",
    diagnosing: "Chẩn đoán",
    quoted: "Đã báo giá",
    approved: "Phê duyệt (APPROVED)",
    in_progress: "Đang sửa chữa",
    finished: "Hoàn thành",
    invoiced: "Đã lập hóa đơn",
    unpaid: "Chưa thanh toán",
    partial: "Thanh toán 1 phần",
    paid: "Đã thanh toán"
  };
  return map[status] || status;
}

// Step 12: 4-Screen Wizard & State Machine Logic
let wizardState = {
  currentStep: 1,
  activeData: null
};

function switchWizardStep(stepNum) {
  wizardState.currentStep = stepNum;
  for (let i = 1; i <= 4; i++) {
    const btn = document.getElementById(`step-btn-${i}`);
    const screen = document.getElementById(`wizard-screen-${i}`);
    if (btn) btn.classList.toggle("active", i === stepNum);
    if (screen) screen.style.display = (i === stepNum) ? "block" : "none";
  }
}

async function submitWizardScreen1() {
  const symptoms = document.getElementById("wz-symptoms-input")?.value || "";
  if (!symptoms.trim()) {
    showToast("Vui lòng nhập mô tả triệu chứng xe!");
    return;
  }
  showToast("AI Engine đang phân tích dữ liệu triệu chứng...");
  try {
    const res = await apiFetch("/ai/assistant", {
      method: "POST",
      body: JSON.stringify({ question: `Lập dự thảo báo giá nháp cho triệu chứng: ${symptoms}` })
    });
    
    renderFormattedAIOutput("wz-ai-diag-output", res.output);
    switchWizardStep(2);
  } catch (err) {
    showToast(`Lỗi phân tích AI: ${err.message}`);
  }
}

function proceedToScreen3() {
  switchWizardStep(3);
  renderWizardReviewTable();
}

function proceedToScreen4() {
  switchWizardStep(4);
}

function renderWizardReviewTable() {
  const tbody = document.getElementById("wz-review-items-tbody");
  if (!tbody) return;
  tbody.innerHTML = `
    <tr>
      <td><code>PAR-OIL-001</code></td>
      <td>Dầu nhớt động cơ Synthetic 4L</td>
      <td>4</td>
      <td>250,000 VNĐ</td>
      <td><span style="color: #10b981; font-weight:700;">25 (Đủ tồn kho)</span></td>
      <td style="color: #34d399; font-weight:700;">1,000,000 VNĐ</td>
    </tr>
    <tr>
      <td><code>PAR-FIL-001</code></td>
      <td>Lọc nhớt động cơ chính hãng</td>
      <td>1</td>
      <td>150,000 VNĐ</td>
      <td><span style="color: #10b981; font-weight:700;">18 (Đủ tồn kho)</span></td>
      <td style="color: #34d399; font-weight:700;">150,000 VNĐ</td>
    </tr>
    <tr>
      <td><code>SER-002</code></td>
      <td>Công láng đĩa phanh & Bảo dưỡng heo phanh</td>
      <td>1</td>
      <td>400,000 VNĐ</td>
      <td>-</td>
      <td style="color: #34d399; font-weight:700;">400,000 VNĐ</td>
    </tr>
  `;
  const reviewTotal = document.getElementById("wz-review-total");
  if (reviewTotal) reviewTotal.innerText = "1,550,000 VNĐ";
  const finalTotal = document.getElementById("wz-final-total-display");
  if (finalTotal) finalTotal.innerText = "1,550,000 VNĐ";
}

// Step 13: 5 Demo Scenario Launchers
async function triggerDemoScenarioUI(scenarioId) {
  showToast(`Đang thực thi Kịch bản Demo ${scenarioId}...`);
  try {
    const res = await apiFetch(`/ai/demo-scenarios/${scenarioId}`, { method: "POST" });
    wizardState.activeData = res;
    
    const symEl = document.getElementById("wz-symptoms-input");
    if (symEl) symEl.value = res.symptoms;
    
    const warnHtml = res.warnings && res.warnings.length > 0 ? 
      `<div style="background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.3); padding: 0.85rem; border-radius: var(--radius-md); margin-top: 1rem; color: #f43f5e; font-weight: 700;">
        ${res.warnings.join('<br>')}
      </div>` : '';
      
    const diagOut = document.getElementById("wz-ai-diag-output");
    if (diagOut) {
      diagOut.innerHTML = `
        <div style="font-weight:700; color: var(--accent-purple); margin-bottom: 0.5rem;">[${res.scenario_title}]</div>
        <div><strong>Chẩn đoán:</strong> ${res.diagnosis}</div>
        <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">${res.ai_raw_output}</div>
      `;
    }
    const warnBox = document.getElementById("wz-ai-warnings-box");
    if (warnBox) warnBox.innerHTML = warnHtml;

    const tbody = document.getElementById("wz-review-items-tbody");
    if (tbody) {
      tbody.innerHTML = "";
      (res.suggested_parts || []).forEach(p => {
        const stockCol = p.stock === 0 ? 
          `<span style="color: #f43f5e; font-weight:800;">0 (⚠️ HẾT HÀNG KHO)</span>` : 
          `<span style="color: #10b981; font-weight:700;">${p.stock} (Còn hàng)</span>`;
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><code>${p.code}</code></td>
          <td>${p.name}</td>
          <td>${p.qty}</td>
          <td>${p.price.toLocaleString()} VNĐ</td>
          <td>${stockCol}</td>
          <td style="color: #34d399; font-weight:700;">${p.total.toLocaleString()} VNĐ</td>
        `;
        tbody.appendChild(tr);
      });

      (res.suggested_services || []).forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><code>${s.code}</code></td>
          <td>${s.name} (Dịch vụ)</td>
          <td>1</td>
          <td>${s.cost.toLocaleString()} VNĐ</td>
          <td>-</td>
          <td style="color: #34d399; font-weight:700;">${s.cost.toLocaleString()} VNĐ</td>
        `;
        tbody.appendChild(tr);
      });
    }

    const fmtTotal = `${(res.estimated_total || 0).toLocaleString('vi-VN')} VNĐ`;
    const reviewTotal = document.getElementById("wz-review-total");
    if (reviewTotal) reviewTotal.innerText = fmtTotal;
    const finalTotal = document.getElementById("wz-final-total-display");
    if (finalTotal) finalTotal.innerText = fmtTotal;

    switchWizardStep(2);
    showToast(`Đã tải Kịch bản ${scenarioId}: ${res.scenario_title}`);
  } catch (err) {
    showToast(`Lỗi chạy kịch bản: ${err.message}`);
  }
}

// Step 11: Load Evaluation Report
async function loadAIBenchmarkReport() {
  const container = document.getElementById("ai-benchmark-container");
  if (container) container.style.display = "block";
  try {
    const data = await apiFetch("/ai/evaluation-report");
    const top1 = document.getElementById("bm-top1");
    if (top1) top1.innerText = `${data.top1_accuracy_percent}%`;
    const parts = document.getElementById("bm-parts");
    if (parts) parts.innerText = `${data.parts_accuracy_percent}%`;
    const pvar = document.getElementById("bm-price-var");
    if (pvar) pvar.innerText = `${data.price_variance_percent}%`;
    const lat = document.getElementById("bm-latency");
    if (lat) lat.innerText = `${data.average_latency_ms} ms`;
    const cost = document.getElementById("bm-cost");
    if (cost) cost.innerText = `$${data.total_estimated_cost_usd}`;
    showToast("Đã tải Báo cáo Đo lường & Đánh giá AI Engine!");
  } catch (err) {
    showToast(`Lỗi tải báo cáo: ${err.message}`);
  }
}

function triggerApprovedPayment() {
  openPaymentModal(999, "INV-2026-FINAL", 1550000);
}

// Interactive Chatbot Engine
async function sendAIChatMessage() {
  const inputEl = document.getElementById("ai-chat-input");
  const text = (inputEl ? inputEl.value || "" : "").trim();
  if (!text) return;

  appendChatMessage("user", text);
  if (inputEl) inputEl.value = "";

  const typingId = appendChatMessage("ai", "<em>AI Assistant đang phân tích dữ liệu...</em>");

  try {
    const res = await apiFetch("/ai/assistant", {
      method: "POST",
      body: JSON.stringify({ question: text })
    });

    const streamEl = document.getElementById("ai-chat-stream");
    const typingBubble = document.getElementById(typingId);
    if (typingBubble && streamEl) streamEl.removeChild(typingBubble);

    appendChatMessage("ai", res.output || "AI không thể đưa ra phản hồi.");
  } catch (err) {
    appendChatMessage("ai", `❌ Lỗi kết nối AI Engine: ${err.message}`);
  }
}

function triggerQuickPrompt(promptKey) {
  const promptsMap = {
    vios_vibration: "Xe Toyota Vios 2018 bị rung khi chạy không tải thì có thể do đâu?",
    history_analysis: "Phân tích lịch sử sửa chữa xe 51H-888.88",
    draft_mazda: "Xe Mazda 3 cần thay dầu máy, lọc dầu và kiểm tra phanh.",
    business_analysis: "Doanh thu tháng này thế nào?",
    predict_maintenance: "Dự đoán bảo dưỡng đợt tiếp theo cho xe 51H-888.88",
    customer_progress: "Xe của tôi đang sửa đến đâu rồi?"
  };

  const text = promptsMap[promptKey] || promptKey;
  const inputEl = document.getElementById("ai-chat-input");
  if (inputEl) {
    inputEl.value = text;
    sendAIChatMessage();
  }
}

function appendChatMessage(sender, htmlContent) {
  const stream = document.getElementById("ai-chat-stream");
  if (!stream) return;

  const msgId = `chat-msg-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
  const div = document.createElement("div");
  div.id = msgId;
  div.className = `chat-msg ${sender}-msg`;
  div.style.display = "flex";
  div.style.gap = "0.75rem";
  div.style.alignItems = "flex-start";

  if (sender === "user") {
    div.style.justifyContent = "flex-end";
    div.innerHTML = `
      <div style="background: var(--accent-primary); color: white; padding: 0.75rem 1rem; border-radius: 14px; border-top-right-radius: 2px; max-width: 80%; font-size: 0.9rem; line-height: 1.5;">
        ${escapeHTML(htmlContent)}
      </div>
      <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--bg-card-hover); border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; color: var(--text-main); font-size: 0.85rem; flex-shrink: 0;">
        <i class="fa-solid fa-user"></i>
      </div>
    `;
  } else {
    let formatted = htmlContent
      .replace(/### (.*?)\n/g, '<strong style="color:var(--accent-cyan); font-size: 1rem; display:block; margin-bottom:0.4rem;">$1</strong>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

    div.innerHTML = `
      <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--accent-purple); display: flex; align-items: center; justify-content: center; color: white; font-size: 0.85rem; flex-shrink: 0;">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.85rem 1.1rem; border-radius: 14px; border-top-left-radius: 2px; max-width: 85%; font-size: 0.9rem; line-height: 1.6; color: var(--text-main);">
        ${formatted}
      </div>
    `;
  }

  stream.appendChild(div);
  stream.scrollTop = stream.scrollHeight;
  return msgId;
}

function clearAIChatHistory() {
  const stream = document.getElementById("ai-chat-stream");
  if (stream) {
    stream.innerHTML = `
      <div class="chat-msg ai-msg" style="display: flex; gap: 0.75rem; align-items: flex-start;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--accent-purple); display: flex; align-items: center; justify-content: center; color: white; font-size: 0.85rem; flex-shrink: 0;">
          <i class="fa-solid fa-robot"></i>
        </div>
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 0.85rem 1.1rem; border-radius: 14px; border-top-left-radius: 2px; max-width: 85%; font-size: 0.9rem; line-height: 1.6; color: var(--text-main);">
          Lịch sử cuộc trò chuyện đã được làm sạch. Bạn cần AI hỗ trợ thêm thông tin gì?
        </div>
      </div>
    `;
  }
}

async function submitOBDDiagnosticForm(event) {
  if (event && event.preventDefault) event.preventDefault();
  const brand = document.getElementById("obd-brand")?.value || "Toyota";
  const model = document.getElementById("obd-model")?.value || "Camry";
  const year = parseInt(document.getElementById("obd-year")?.value || 2022);
  const mileage = parseInt(document.getElementById("obd-mileage")?.value || 40000);
  const obd_code = document.getElementById("obd-code")?.value || "P0300";
  const symptoms = document.getElementById("obd-symptoms")?.value || "";

  const card = document.getElementById("obd-output-card");
  const content = document.getElementById("obd-output-content");
  if (card) card.style.display = "block";
  if (content) content.innerHTML = `<em style="color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> AI Engine đang phân tích mã lỗi OBD-II ${obd_code}...</em>`;

  try {
    const res = await apiFetch("/ai/obd-diagnostic", {
      method: "POST",
      body: JSON.stringify({ brand, model, year, mileage, obd_code, symptoms })
    });

    let formatted = (res.output || "")
      .replace(/### (.*?)\n/g, '<h5 style="color:var(--accent-cyan); margin-bottom:0.5rem;">$1</h5>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    if (content) content.innerHTML = formatted;
    showToast(`Đã hoàn tất phân tích mã lỗi OBD: ${obd_code}`);
  } catch (err) {
    if (content) content.innerHTML = `<span style="color: var(--accent-rose);">❌ Lỗi phân tích OBD: ${err.message}</span>`;
  }
}

// Customer Portal Registration & Phone Contact Popup Handlers
async function submitCustomerPortalRegistration(e) {
  if (e && e.preventDefault) e.preventDefault();
  
  const submitBtn = document.getElementById("btn-submit-request");
  const name = document.getElementById("cp-cust-name")?.value.trim() || "";
  const phone = document.getElementById("cp-cust-phone")?.value.trim() || "";
  const email = document.getElementById("cp-cust-email")?.value.trim() || "";
  const address = document.getElementById("cp-cust-address")?.value.trim() || "";
  
  const plate = document.getElementById("cp-veh-plate")?.value.trim() || "";
  const brand = document.getElementById("cp-veh-brand")?.value.trim() || "Toyota";
  const model = document.getElementById("cp-veh-model")?.value.trim() || "Vios";
  const year = parseInt(document.getElementById("cp-veh-year")?.value || 2020);
  const mileage = parseInt(document.getElementById("cp-veh-mileage")?.value || 50000);
  
  const serviceType = document.getElementById("cp-service-type")?.value || "Bảo dưỡng định kỳ";
  const description = document.getElementById("cp-symptoms")?.value.trim() || "";
  const preferredDate = document.getElementById("cp-pref-date")?.value || "";
  const preferredTime = document.getElementById("cp-pref-time")?.value || "09:00";
  const note = document.getElementById("cp-note")?.value.trim() || "";

  // Frontend Validation Check
  if (!name || !phone || !plate || !serviceType) {
    showToast("Vui lòng điền đầy đủ các thông tin bắt buộc (*)");
    return;
  }

  // Section 16: Anti-Duplicate Submission - Disable button immediately
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang gửi...';
  }

  try {
    const payload = {
      fullName: name,
      phone: phone,
      email: email || null,
      address: address || null,
      licensePlate: plate,
      vehicleBrand: brand,
      vehicleModel: model,
      manufactureYear: year,
      currentMileage: mileage,
      serviceType: serviceType,
      description: description || null,
      preferredDate: preferredDate || null,
      preferredTime: preferredTime || null,
      note: note || null
    };

    const res = await apiFetch("/customer-requests", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    const reqCode = res.requestCode || res.code || "REQ-SUCCESS";

    // Section 17: UX Success Feedback
    const modalContent = `
      <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem; color: #10b981; margin-bottom: 0.5rem;"><i class="fa-solid fa-circle-check"></i></div>
        <h3 style="font-family: Arial; font-size: 1.35rem; color: var(--text-main); margin-bottom: 0.5rem;">Gửi Yêu Cầu Thành Công!</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.25rem;">Gara VTV sẽ liên hệ với quý khách theo SĐT <strong>${phone}</strong> trong thời gian sớm nhất.</p>
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;">
          <div style="font-size: 0.8rem; color: #38bdf8; font-weight: 600; text-transform: uppercase;">Mã Yêu Cầu Của Bạn</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: var(--accent-cyan); letter-spacing: 0.05em; font-family: monospace;">${reqCode}</div>
        </div>
        <div style="display: flex; gap: 0.75rem; justify-content: center;">
          <button class="btn btn-secondary" onclick="closeModal('modal-ai-dialog')">Đóng</button>
          <button class="btn btn-primary" onclick="closeModal('modal-ai-dialog'); openTrackRequestModal('${reqCode}');">
            <i class="fa-solid fa-magnifying-glass"></i> Xem Trạng Thái Yêu Cầu
          </button>
        </div>
      </div>
    `;

    openModal("modal-ai-dialog", "Thông Báo Tiếp Nhận Yêu Cầu", modalContent);
    
    const form = document.getElementById("form-customer-portal");
    if (form) form.reset();

  } catch (err) {
    showToast(`❌ Không thể gửi yêu cầu: ${err.message || 'Vui lòng thử lại sau.'}`);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Gửi Yêu Cầu';
    }
  }
}

function openPhoneContactModal() {
  openModal("modal-phone-contact");
}

function submitCallbackRequest(e) {
  if (e && e.preventDefault) e.preventDefault();
  const phone = document.getElementById("cb-phone")?.value || "";
  const time = document.getElementById("cb-time")?.value || "immediate";

  if (!phone.trim()) {
    showToast("Vui lòng nhập số điện thoại liên hệ!");
    return;
  }

  closeModal("modal-phone-contact");
  showToast(`Đã ghi nhận yêu cầu gọi lại cho SĐT: ${phone}! Kỹ thuật viên sẽ liên hệ lại ngay trong 5 phút.`);
  
  const phoneInput = document.getElementById("cb-phone");
  if (phoneInput) phoneInput.value = "";
}

async function lookupCustomerVehicleProgress() {
  const input = document.getElementById("cust-search-plate")?.value?.trim();
  const resContainer = document.getElementById("cust-progress-result");
  if (!resContainer) return;

  if (!input) {
    showToast("Vui lòng nhập biển số xe hoặc mã phiếu sửa chữa!");
    return;
  }

  resContainer.style.display = "block";
  resContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 1rem;"><i class="fa-solid fa-spinner fa-spin"></i> Đang tìm kiếm thông tin xe ${input}...</div>`;

  try {
    const roList = await apiFetch("/repair-orders");
    const matched = roList.find(ro => 
      ro.code.toLowerCase().includes(input.toLowerCase()) || 
      (ro.license_plate && ro.license_plate.toLowerCase().includes(input.toLowerCase()))
    );

    if (matched) {
      const statusMap = {
        received: { text: "Đã Tiếp Nhận Xe", color: "#38bdf8", icon: "fa-car-tunnel" },
        diagnosing: { text: "KTV Đang Kiểm Tra & Lập Báo Giá", color: "#fbbf24", icon: "fa-stethoscope" },
        in_progress: { text: "Đang Sửa Chữa Tại Xưởng", color: "#a855f7", icon: "fa-wrench" },
        completed: { text: "Đã Hoàn Thành - Sẵn Sàng Giao Xe", color: "#34d399", icon: "fa-circle-check" },
        closed: { text: "Đã Thanh Toán & Đã Giao Xe", color: "#94a3b8", icon: "fa-flag-checkered" }
      };
      const st = statusMap[matched.status] || { text: matched.status, color: "#cbd5e1", icon: "fa-info-circle" };

      resContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.85rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
          <div>
            <h4 style="font-family: Arial; margin: 0; color: var(--text-main); font-size: 1.15rem; display: flex; align-items: center; gap: 0.5rem;">
              <i class="fa-solid fa-car" style="color: var(--accent-primary);"></i> Xe: ${matched.license_plate || input.toUpperCase()}
            </h4>
            <span style="font-size: 0.82rem; color: var(--text-muted);">Mã Phiếu: <strong>${matched.code}</strong> | Ngày nhận: ${new Date(matched.created_at || Date.now()).toLocaleDateString('vi-VN')}</span>
          </div>
          <span style="background: ${st.color}20; color: ${st.color}; border: 1px solid ${st.color}50; font-size: 0.82rem; font-weight: 700; padding: 4px 12px; border-radius: 12px; display: inline-flex; align-items: center; gap: 0.35rem;">
            <i class="fa-solid ${st.icon}"></i> ${st.text}
          </span>
        </div>
        <div style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">
          <div><strong>Triệu chứng ban đầu:</strong> ${matched.initial_symptoms || 'Bảo dưỡng định kỳ'}</div>
          <div><strong>Chẩn đoán kỹ thuật:</strong> ${matched.technical_diagnosis || 'KTV đang tiến hành phân tích hạng mục'}</div>
          <div style="margin-top: 0.5rem; color: var(--accent-cyan); font-weight: 600;">Tổng chi phí dự toán: ${(matched.final_cost || 0).toLocaleString('vi-VN')} VNĐ</div>
        </div>
      `;
    } else {
      resContainer.innerHTML = `
        <div style="text-align: center; color: var(--accent-rose); padding: 1rem;">
          <i class="fa-solid fa-circle-exclamation" style="font-size: 1.5rem; margin-bottom: 0.5rem;"></i>
          <div>Không tìm thấy dữ liệu cho <strong>"${input}"</strong>. Xe mới có thể đang được Lễ tân tiếp nhận tại quầy.</div>
        </div>
      `;
    }
  } catch (err) {
    resContainer.innerHTML = `<div style="color: var(--accent-rose); text-align: center;">❌ Đã xảy ra lỗi khi tra cứu. Vui lòng liên hệ Hotline 033.344.2358.</div>`;
  }
}

// Global Window Bindings for HTML Inline Event Handlers
window.toggleTheme = toggleTheme;
window.toggleMobileSidebar = toggleMobileSidebar;
window.switchView = switchView;
window.openModal = openModal;
window.closeModal = closeModal;
window.showToast = showToast;
window.submitNewAppointment = submitNewAppointment;
window.submitNewRO = submitNewRO;
window.submitNewCustomer = submitNewCustomer;
window.submitPayment = submitPayment;
window.openRODetailModal = openRODetailModal;
window.saveTechDiagnosis = saveTechDiagnosis;
window.addItemToRO = addItemToRO;
window.deleteROItem = deleteROItem;
window.createInvoiceFromRODetail = createInvoiceFromRODetail;
window.triggerAIFromRODetail = triggerAIFromRODetail;
window.openPaymentModal = openPaymentModal;
window.updateQRAmountLive = updateQRAmountLive;
window.togglePaymentMethodFields = togglePaymentMethodFields;
window.copyTextToClipboard = copyTextToClipboard;
window.switchWizardStep = switchWizardStep;
window.submitWizardScreen1 = submitWizardScreen1;
window.proceedToScreen3 = proceedToScreen3;
window.proceedToScreen4 = proceedToScreen4;
window.triggerDemoScenarioUI = triggerDemoScenarioUI;
window.loadAIBenchmarkReport = loadAIBenchmarkReport;
window.triggerApprovedPayment = triggerApprovedPayment;
window.setModalAIQuestion = setModalAIQuestion;
window.submitModalAIQuestion = submitModalAIQuestion;
window.copyAIResult = copyAIResult;
window.setFreeQuestion = setFreeQuestion;
window.runAISandbox = runAISandbox;
window.applyPromptTemplate = applyPromptTemplate;
window.copyAISandboxResult = copyAISandboxResult;
window.runAIServiceExplainer = runAIServiceExplainer;
window.runAIDraftQuotation = runAIDraftQuotation;
window.runAIHistorySummary = runAIHistorySummary;
window.sendAIChatMessage = sendAIChatMessage;
window.triggerQuickPrompt = triggerQuickPrompt;
window.clearAIChatHistory = clearAIChatHistory;
window.submitOBDDiagnosticForm = submitOBDDiagnosticForm;
window.toggleItemSelectType = toggleItemSelectType;
window.switchAISubTab = switchAISubTab;
window.submitCustomerPortalRegistration = submitCustomerPortalRegistration;
window.openPhoneContactModal = openPhoneContactModal;
window.submitCallbackRequest = submitCallbackRequest;
window.lookupCustomerVehicleProgress = lookupCustomerVehicleProgress;
window.initDatepickers = initDatepickers;
window.logoutUser = logoutUser;
window.checkAuthPermission = checkAuthPermission;

// ----------------------------------------------------
// CUSTOMER REQUESTS MANAGEMENT & REAL-TIME SSE LOGIC
// ----------------------------------------------------

let sseEventSource = null;

function initSSERealtimeStream() {
  if (sseEventSource) return;
  const streamUrl = `${API_BASE}/customer-requests/stream`;
  try {
    sseEventSource = new EventSource(streamUrl);
    sseEventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "NEW_CUSTOMER_REQUEST") {
          const req = payload.data;
          showToast(`🔔 CÓ YÊU CẦU MỚI: ${req.fullName} - ${req.vehicleBrand} ${req.vehicleModel} (${req.licensePlate})!`);
          
          // Increment badge count
          const badge = document.getElementById("nav-badge-requests");
          if (badge) {
            let count = parseInt(badge.textContent || "0") + 1;
            badge.textContent = count;
            badge.style.display = "inline-block";
          }
          
          // Refresh table if active view is customer-requests
          if (currentState.activeView === "customer-requests") {
            loadCustomerRequestsFromBackend();
          }
        } else if (payload.event === "UPDATE_CUSTOMER_REQUEST") {
          if (currentState.activeView === "customer-requests") {
            loadCustomerRequestsFromBackend();
          }
        }
      } catch (e) { console.error("SSE parse:", e); }
    };
  } catch (e) {
    console.log("SSE stream notice:", e);
  }
}

async function loadCustomerRequestsFromBackend() {
  try {
    const list = await apiFetch("/customer-requests");
    currentState.customerRequests = Array.isArray(list) ? list : [];
    
    // Update KPI counters
    let pending = 0, confirmed = 0, inprogress = 0, completed = 0;
    currentState.customerRequests.forEach(r => {
      if (r.status === "Pending") pending++;
      else if (r.status === "Contacted" || r.status === "Confirmed") confirmed++;
      else if (r.status === "InProgress") inprogress++;
      else if (r.status === "Completed") completed++;
    });

    const pEl = document.getElementById("req-kpi-pending");
    if (pEl) pEl.textContent = pending;
    
    const cEl = document.getElementById("req-kpi-confirmed");
    if (cEl) cEl.textContent = confirmed;
    
    const iEl = document.getElementById("req-kpi-inprogress");
    if (iEl) iEl.textContent = inprogress;
    
    const dEl = document.getElementById("req-kpi-completed");
    if (dEl) dEl.textContent = completed;

    // Update nav badge count for Pending requests
    const badge = document.getElementById("nav-badge-requests");
    if (badge) {
      if (pending > 0) {
        badge.textContent = pending;
        badge.style.display = "inline-block";
      } else {
        badge.style.display = "none";
      }
    }

    renderCustomerRequestsTable();
  } catch (err) {
    console.error("loadCustomerRequestsFromBackend:", err);
  }
}

function filterCustomerRequestsTable() {
  renderCustomerRequestsTable();
}

function renderCustomerRequestsTable() {
  const tbody = document.getElementById("customer-requests-tbody");
  if (!tbody) return;

  const search = document.getElementById("req-search-input")?.value?.toLowerCase()?.trim() || "";
  const statusFilter = document.getElementById("req-status-filter")?.value || "ALL";

  let list = currentState.customerRequests || [];

  if (statusFilter !== "ALL") {
    list = list.filter(r => r.status === statusFilter);
  }

  if (search) {
    list = list.filter(r => 
      (r.requestCode && r.requestCode.toLowerCase().includes(search)) ||
      (r.fullName && r.fullName.toLowerCase().includes(search)) ||
      (r.phone && r.phone.toLowerCase().includes(search)) ||
      (r.licensePlate && r.licensePlate.toLowerCase().includes(search)) ||
      (r.serviceType && r.serviceType.toLowerCase().includes(search))
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 2rem;">
          Không tìm thấy yêu cầu dịch vụ nào phù hợp.
        </td>
      </tr>
    `;
    return;
  }

  const statusMap = {
    Pending: { label: "Mới (Pending)", color: "#fb7185", bg: "rgba(244, 63, 94, 0.15)" },
    Contacted: { label: "Đã Liên Hệ", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    Confirmed: { label: "Đã Xác Nhận", color: "#2563eb", bg: "rgba(37, 99, 235, 0.15)" },
    InProgress: { label: "Đang Xử Lý", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    Completed: { label: "Hoàn Thành", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    Cancelled: { label: "Đã Hủy", color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)" }
  };

  tbody.innerHTML = list.map(r => {
    const st = statusMap[r.status] || { label: r.status, color: "#cbd5e1", bg: "rgba(255,255,255,0.1)" };
    const dateStr = formatVietnameseDate(r.createdAt || Date.now());

    return `
      <tr>
        <td><strong style="color: var(--accent-cyan); font-family: monospace;">${r.requestCode || ('REQ-' + r.id)}</strong></td>
        <td><strong>${r.fullName}</strong></td>
        <td><a href="tel:${r.phone}" style="color: var(--accent-primary); text-decoration: none;">${r.phone}</a></td>
        <td><span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-weight: 700;">${r.licensePlate}</span></td>
        <td>${r.vehicleBrand} ${r.vehicleModel}</td>
        <td>${r.serviceType}</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${dateStr}</td>
        <td>
          <span style="background: ${st.bg}; color: ${st.color}; font-size: 0.78rem; font-weight: 700; padding: 4px 10px; border-radius: 12px; display: inline-block;">
            ${st.label}
          </span>
        </td>
        <td>
          <div style="display: flex; gap: 0.35rem;">
            <button class="btn btn-secondary btn-sm" onclick="openCustomerRequestDetailModal(${r.id})" title="Xem chi tiết & Xử lý">
              <i class="fa-solid fa-eye"></i> Xem & Xử Lý
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

async function openCustomerRequestDetailModal(reqId) {
  try {
    const req = await apiFetch(`/customer-requests/${reqId}`);
    if (!req) return;

    const modalContent = `
      <div style="display: flex; flex-direction: column; gap: 1.25rem;">
        <!-- Header Info -->
        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 0.85rem 1.1rem;">
          <div>
            <div style="font-size: 0.75rem; color: #38bdf8; font-weight: 700; text-transform: uppercase;">MÃ YÊU CẦU DỊCH VỤ</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: var(--text-main); font-family: monospace;">${req.requestCode}</div>
          </div>
          <div>
            <label style="font-size: 0.78rem; color: var(--text-muted); display: block; margin-bottom: 2px;">Cập Nhật Trạng Thái:</label>
            <select id="req-modal-status" class="form-control" style="font-weight: 700; background: var(--bg-card); color: var(--text-main);" onchange="submitUpdateCustomerRequestStatus(${req.id}, this.value)">
              <option value="Pending" ${req.status === 'Pending' ? 'selected' : ''}>Mới (Pending)</option>
              <option value="Contacted" ${req.status === 'Contacted' ? 'selected' : ''}>Đã Liên Hệ (Contacted)</option>
              <option value="Confirmed" ${req.status === 'Confirmed' ? 'selected' : ''}>Đã Xác Nhận Hẹn (Confirmed)</option>
              <option value="InProgress" ${req.status === 'InProgress' ? 'selected' : ''}>Đang Xử Lý tại Xưởng (InProgress)</option>
              <option value="Completed" ${req.status === 'Completed' ? 'selected' : ''}>Hoàn Thành Bàn Giao (Completed)</option>
              <option value="Cancelled" ${req.status === 'Cancelled' ? 'selected' : ''}>Đã Hủy (Cancelled)</option>
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <!-- Customer Info -->
          <div style="background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem;">
            <h4 style="font-family: Arial; font-size: 0.92rem; color: var(--accent-primary); margin-bottom: 0.75rem;"><i class="fa-solid fa-user"></i> THÔNG TIN KHÁCH HÀNG</h4>
            <div style="font-size: 0.85rem; line-height: 1.7; color: var(--text-main);">
              <div><strong>Họ và tên:</strong> ${req.fullName}</div>
              <div><strong>Số điện thoại:</strong> <a href="tel:${req.phone}" style="color: var(--accent-cyan);">${req.phone}</a></div>
              <div><strong>Email:</strong> ${req.email || 'Chưa cung cấp'}</div>
              <div><strong>Địa chỉ:</strong> ${req.address || 'Chưa cung cấp'}</div>
            </div>
          </div>

          <!-- Vehicle Info -->
          <div style="background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem;">
            <h4 style="font-family: Arial; font-size: 0.92rem; color: var(--accent-cyan); margin-bottom: 0.75rem;"><i class="fa-solid fa-car"></i> THÔNG TIN XE</h4>
            <div style="font-size: 0.85rem; line-height: 1.7; color: var(--text-main);">
              <div><strong>Biển số xe:</strong> <span style="color: var(--accent-cyan); font-weight: 700;">${req.licensePlate}</span></div>
              <div><strong>Hãng & Dòng xe:</strong> ${req.vehicleBrand} ${req.vehicleModel}</div>
              <div><strong>Năm sản xuất:</strong> ${req.manufactureYear || '2020'}</div>
              <div><strong>Số km Odometer:</strong> ${req.currentMileage ? req.currentMileage.toLocaleString() + ' km' : 'Chưa nhập'}</div>
            </div>
          </div>
        </div>

        <!-- Service Request Info -->
        <div style="background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem;">
          <h4 style="font-family: Arial; font-size: 0.92rem; color: var(--accent-purple); margin-bottom: 0.75rem;"><i class="fa-solid fa-wrench"></i> NỘI DUNG YÊU CẦU DỊCH VỤ</h4>
          <div style="font-size: 0.85rem; line-height: 1.7; color: var(--text-main);">
            <div><strong>Loại dịch vụ:</strong> <span style="color: #fb7185; font-weight: 700;">${req.serviceType}</span></div>
            <div><strong>Mô tả chi tiết:</strong> ${req.description || 'Không có mô tả chi tiết'}</div>
            <div><strong>Thời gian mong muốn mang xe đến:</strong> ${req.preferredDate ? (req.preferredDate + ' lúc ' + (req.preferredTime || '09:00')) : 'Lễ tân xếp lịch'}</div>
            <div><strong>Ghi chú từ khách:</strong> ${req.note || 'Không có ghi chú'}</div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.5rem;">Thời gian gửi: ${formatVietnameseDate(req.createdAt)}</div>
          </div>
        </div>

        <!-- Admin Processing Notes & Staff Assignment -->
        <div style="background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem;">
          <h4 style="font-family: Arial; font-size: 0.92rem; color: var(--accent-amber); margin-bottom: 0.75rem;"><i class="fa-solid fa-user-gear"></i> XỬ LÝ & GHI CHÚ QUẢN TRỊ</h4>
          <div style="display: flex; flex-direction: column; gap: 0.75rem;">
            <div>
              <label style="font-size: 0.8rem; color: var(--text-muted);">Ghi Chú Admin (Ví dụ: Đã gọi khách, xác nhận đến lúc 9:00):</label>
              <div style="display: flex; gap: 0.5rem; margin-top: 4px;">
                <input type="text" id="req-modal-admin-note" class="form-control" value="${req.adminNote || ''}" placeholder="Nhập ghi chú xử lý...">
                <button class="btn btn-secondary btn-sm" onclick="submitSaveCustomerRequestNote(${req.id})">Lưu Ghi Chú</button>
              </div>
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 0.5rem;">
          <button class="btn btn-secondary" onclick="closeModal('modal-ai-dialog')">Đóng</button>
          <button class="btn btn-primary" onclick="convertRequestToRepairOrder(${req.id})">
            <i class="fa-solid fa-file-circle-plus"></i> Tạo Phiếu Sửa Chữa (RO)
          </button>
        </div>
      </div>
    `;

    openModal("modal-ai-dialog", `Chi Tiết Yêu Cầu ${req.requestCode}`, modalContent);
  } catch (err) {
    showToast("Không thể tải chi tiết yêu cầu!");
  }
}

async function submitUpdateCustomerRequestStatus(reqId, newStatus) {
  try {
    await apiFetch(`/customer-requests/${reqId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus })
    });
    showToast(`Đã cập nhật trạng thái yêu cầu sang: ${newStatus}`);
    await loadCustomerRequestsFromBackend();
  } catch (err) {
    showToast("❌ Không thể cập nhật trạng thái!");
  }
}

async function submitSaveCustomerRequestNote(reqId) {
  const note = document.getElementById("req-modal-admin-note")?.value?.trim();
  if (!note) {
    showToast("Vui lòng nhập ghi chú!");
    return;
  }
  try {
    await apiFetch(`/customer-requests/${reqId}/note`, {
      method: "POST",
      body: JSON.stringify({ admin_note: note })
    });
    showToast("Đã lưu ghi chú Admin thành công!");
    await loadCustomerRequestsFromBackend();
  } catch (err) {
    showToast("❌ Không thể lưu ghi chú!");
  }
}

async function convertRequestToRepairOrder(reqId) {
  try {
    const req = await apiFetch(`/customer-requests/${reqId}`);
    if (!req) return;

    // Auto-update status to InProgress
    await apiFetch(`/customer-requests/${reqId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: "InProgress" })
    });

    closeModal('modal-ai-dialog');
    switchView('repair-orders');
    openModal('modal-new-ro');
    
    // Auto-fill new RO modal fields
    setTimeout(() => {
      const plateEl = document.getElementById('ro-plate-input');
      if (plateEl) plateEl.value = req.licensePlate;
      
      const symEl = document.getElementById('ro-symptoms-input');
      if (symEl) symEl.value = `[Từ Yêu Cầu ${req.requestCode}] ${req.serviceType}: ${req.description || ''}`;
    }, 300);

    showToast(`Đã chuyển yêu cầu ${req.requestCode} sang tạo Phiếu Sửa Chữa (RO)!`);
  } catch (err) {
    showToast("❌ Không thể tạo phiếu sửa chữa từ yêu cầu này!");
  }
}

// PUBLIC CUSTOMER REQUEST STATUS TRACKING (SECTION 12)
async function openTrackRequestModal(requestCode = "") {
  const codePrompt = requestCode || prompt("Nhập Mã Yêu Cầu của bạn (Ví dụ: REQ-20260829-0001):");
  if (!codePrompt) return;

  try {
    const req = await apiFetch(`/customer-requests/code/${codePrompt.trim().toUpperCase()}`);
    
    const steps = [
      { key: "Pending", title: "1. Đã Gửi Yêu Cầu", desc: "Hệ thống đã tiếp nhận form đăng ký" },
      { key: "Contacted", title: "2. Admin Đã Liên Hệ", desc: "Lễ tân đã gọi điện thoại xác nhận" },
      { key: "Confirmed", title: "3. Đã Xác Nhận Hẹn", desc: "Đã chốt lịch hẹn mang xe đến xưởng" },
      { key: "InProgress", title: "4. Đang Sửa Chữa", desc: "KTV đang bảo dưỡng / sửa chữa tại xưởng" },
      { key: "Completed", title: "5. Hoàn Thành", desc: "Đã bàn giao xe cho khách hàng" }
    ];

    const statusOrder = ["Pending", "Contacted", "Confirmed", "InProgress", "Completed"];
    const currentIdx = statusOrder.indexOf(req.status);

    const stepsHtml = steps.map((s, idx) => {
      const isDone = currentIdx >= idx && req.status !== 'Cancelled';
      const isCurrent = currentIdx === idx && req.status !== 'Cancelled';
      const icon = isDone ? "fa-circle-check" : "fa-circle";
      const color = isDone ? "#10b981" : "var(--text-muted)";
      const bg = isCurrent ? "rgba(16, 185, 129, 0.15)" : "transparent";

      return `
        <div style="display: flex; align-items: center; gap: 0.85rem; padding: 0.75rem; border-radius: 10px; background: ${bg}; margin-bottom: 0.5rem; border: 1px solid ${isCurrent ? '#10b98150' : 'transparent'};">
          <i class="fa-solid ${icon}" style="color: ${color}; font-size: 1.25rem;"></i>
          <div>
            <div style="font-weight: 700; color: ${isDone ? 'var(--text-main)' : 'var(--text-muted)'}; font-size: 0.9rem;">${s.title}</div>
            <div style="font-size: 0.78rem; color: var(--text-muted);">${s.desc}</div>
          </div>
        </div>
      `;
    }).join("");

    const isCancelled = req.status === "Cancelled";

    const modalContent = `
      <div style="padding: 0.5rem 0;">
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 1rem; margin-bottom: 1.25rem;">
          <div style="font-size: 0.78rem; color: #38bdf8; font-weight: 700;">TRA CỨU TRẠNG THÁI YÊU CẦU</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: var(--accent-cyan); font-family: monospace;">${req.requestCode}</div>
          <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">Khách hàng: <strong>${req.fullName}</strong> (${req.phone}) | Xe: <strong>${req.licensePlate}</strong></div>
        </div>

        ${isCancelled ? `
          <div style="background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 12px; padding: 1rem; color: #fb7185; margin-bottom: 1rem; text-align: center;">
            <i class="fa-solid fa-circle-xmark" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
            <div style="font-weight: 700; font-size: 1.05rem;">Yêu cầu dịch vụ này đã bị hủy.</div>
            <div style="font-size: 0.82rem; margin-top: 4px;">Ghi chú: ${req.adminNote || 'Quý khách vui lòng liên hệ Hotline 033.344.2358 để biết chi tiết.'}</div>
          </div>
        ` : stepsHtml}

        <div style="text-align: right; margin-top: 1.25rem;">
          <button class="btn btn-secondary" onclick="closeModal('modal-ai-dialog')">Đóng</button>
        </div>
      </div>
    `;

    openModal("modal-ai-dialog", `Trạng Thái Yêu Cầu ${req.requestCode}`, modalContent);
  } catch (err) {
    showToast(`❌ ${err.message || 'Không thể tra cứu mã yêu cầu này!'}`);
  }
}

async function submitCreateService(e) {
  e.preventDefault();
  try {
    const code = document.getElementById("service-code")?.value?.trim() || "";
    const name = document.getElementById("service-name")?.value?.trim() || "";
    const cost = parseFloat(document.getElementById("service-cost")?.value) || 0;

    if (!name) {
      showToast("Vui lòng nhập tên dịch vụ!");
      return;
    }

    const payload = {
      code: code || `SER-${String(Date.now()).slice(-4)}`,
      name: name,
      labor_cost: cost,
      description: name
    };

    const res = await apiFetch("/services", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    if (res) {
      showToast(`✅ Đã thêm dịch vụ "${name}" thành công!`);
      closeModal("modal-new-service");
      document.getElementById("form-new-service")?.reset();
      await loadInventory();
    }
  } catch (err) {
    showToast(`❌ ${err.message || "Lỗi khi thêm dịch vụ mới!"}`);
  }
}

async function submitCreatePart(e) {
  e.preventDefault();
  try {
    const code = document.getElementById("part-code")?.value?.trim() || "";
    const name = document.getElementById("part-name")?.value?.trim() || "";
    const price = parseFloat(document.getElementById("part-price")?.value) || 0;
    const stock = parseInt(document.getElementById("part-stock")?.value) || 0;
    const minStock = parseInt(document.getElementById("part-min-stock")?.value) || 5;

    if (!name) {
      showToast("Vui lòng nhập tên phụ tùng!");
      return;
    }

    const payload = {
      code: code || `PAR-${String(Date.now()).slice(-4)}`,
      name: name,
      unit_price: price,
      stock_quantity: stock,
      min_stock_alert: minStock,
      category: "Vật tư"
    };

    const res = await apiFetch("/parts", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    if (res) {
      showToast(`✅ Đã nhập phụ tùng "${name}" thành công!`);
      closeModal("modal-new-part");
      document.getElementById("form-new-part")?.reset();
      await loadInventory();
    }
  } catch (err) {
    showToast(`❌ ${err.message || "Lỗi khi nhập phụ tùng mới!"}`);
  }
}

window.loadCustomerRequestsFromBackend = loadCustomerRequestsFromBackend;
window.filterCustomerRequestsTable = filterCustomerRequestsTable;
window.renderCustomerRequestsTable = renderCustomerRequestsTable;
window.openCustomerRequestDetailModal = openCustomerRequestDetailModal;
window.submitUpdateCustomerRequestStatus = submitUpdateCustomerRequestStatus;
window.submitSaveCustomerRequestNote = submitSaveCustomerRequestNote;
window.convertRequestToRepairOrder = convertRequestToRepairOrder;
window.openTrackRequestModal = openTrackRequestModal;
window.submitCreateService = submitCreateService;
window.submitCreatePart = submitCreatePart;


