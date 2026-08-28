// Garage AI Management System - Frontend App Engine

const API_BASE = "http://127.0.0.1:8000/api/v1";

// Application State
let currentState = {
  currentRole: "receptionist",
  token: null,
  activeView: "dashboard",
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

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupTheme();
  setupNavigation();
  setupRoleSwitcher();
  await loginAsCurrentRole();
  await loadAllData();
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

// Auth & Role Handler
async function loginAsCurrentRole() {
  const creds = ROLE_CREDENTIALS[currentState.currentRole];
  try {
    const formData = new URLSearchParams();
    formData.append("username", creds.username);
    formData.append("password", creds.password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      currentState.token = data.access_token;
    }
  } catch (err) {
    console.error("Lỗi đăng nhập tự động:", err);
  }
}

function setupRoleSwitcher() {
  const roleSelect = document.getElementById("role-select");
  const roleBadge = document.getElementById("role-badge");

  roleSelect.addEventListener("change", async (e) => {
    currentState.currentRole = e.target.value;
    roleBadge.className = `role-badge ${currentState.currentRole}`;
    
    const roleMapText = {
      manager: "Quản Lý",
      receptionist: "Lễ Tân",
      technician: "Kỹ Thuật Viên",
      cashier: "Thu Ngân"
    };
    roleBadge.textContent = roleMapText[currentState.currentRole];

    await loginAsCurrentRole();
    await loadAllData();
  });
}

// Helper fetch wrapper
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (currentState.token) {
    headers["Authorization"] = `Bearer ${currentState.token}`;
  }
  headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: "Lỗi kết nối máy chủ" }));
    throw new Error(errData.detail || "Thao tác thất bại");
  }
  return res.json();
}

// Navigation Handler
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const view = item.getAttribute("data-view");
      switchView(view);
    });
  });
}

function switchView(viewName) {
  currentState.activeView = viewName;

  document.querySelectorAll(".nav-item").forEach(el => {
    if (el.getAttribute("data-view") === viewName) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });

  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.remove("active");
  });

  const activeSec = document.getElementById(`view-${viewName}`);
  if (activeSec) activeSec.classList.add("active");

  const titleMap = {
    dashboard: "Tổng Quan Garage",
    appointments: "Quản Lý Lịch Hẹn & Tiếp Nhận Xe",
    "repair-orders": "Phiếu Sửa Chữa & Chẩn Đoán",
    customers: "Danh Sách Khách Hàng & Xe",
    inventory: "Kho Phụ Tùng & Danh Mục Dịch Vụ",
    invoices: "Hóa Đơn & Thanh Toán",
    "ai-studio": "AI Studio & Prompt Engineering Sandbox"
  };
  document.getElementById("page-title").textContent = titleMap[viewName] || "Garage Management";

  loadAllData();
}

// Data Loaders
async function loadAllData() {
  try {
    if (currentState.activeView === "dashboard") await loadDashboard();
    if (currentState.activeView === "appointments") await loadAppointments();
    if (currentState.activeView === "repair-orders") await loadRepairOrders();
    if (currentState.activeView === "customers") await loadCustomersAndVehicles();
    if (currentState.activeView === "inventory") await loadInventory();
    if (currentState.activeView === "invoices") await loadInvoices();
    if (currentState.activeView === "ai-studio") await loadAISandboxData();
  } catch (err) {
    console.error("Lỗi tải dữ liệu:", err);
  }
}

// 1. Dashboard View Loader
async function loadDashboard() {
  const data = await apiFetch("/analytics/dashboard");
  const kpi = data.kpi;

  document.getElementById("kpi-revenue").textContent = `${kpi.total_revenue.toLocaleString('vi-VN')} VNĐ`;
  document.getElementById("kpi-active-orders").textContent = kpi.active_repair_orders;
  document.getElementById("kpi-pending-apts").textContent = kpi.pending_appointments;
  document.getElementById("kpi-low-stock").textContent = kpi.low_stock_parts_count;

  // Load Recent Orders
  const orders = await apiFetch("/repair-orders");
  const tbody = document.getElementById("dash-orders-tbody");
  tbody.innerHTML = "";

  orders.slice(0, 5).forEach(ro => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${ro.code}</strong></td>
      <td><span style="color: #38bdf8; font-weight: 600;">${ro.vehicle ? ro.vehicle.license_plate : 'N/A'}</span></td>
      <td>${ro.mileage_at_reception.toLocaleString()} km</td>
      <td><span class="status-pill ${ro.status}">${formatStatus(ro.status)}</span></td>
      <td style="color: #34d399; font-weight: 600;">${ro.final_cost.toLocaleString()} VNĐ</td>
    `;
    tbody.appendChild(tr);
  });

  // Load Top Services
  const topContainer = document.getElementById("top-services-list");
  topContainer.innerHTML = "";
  data.top_services.forEach(srv => {
    const item = document.createElement("div");
    item.style.cssText = "display: flex; justify-content: space-between; padding: 0.6rem 0; border-bottom: 1px solid var(--border-color); font-size: 0.9rem;";
    item.innerHTML = `
      <div><strong>${srv.name}</strong><br><span style="color: var(--text-muted); font-size: 0.8rem;">Sử dụng: ${srv.count} lần</span></div>
      <div style="color: #34d399; font-weight: 600;">${srv.revenue.toLocaleString()} VNĐ</div>
    `;
    topContainer.appendChild(item);
  });
}

// 2. Appointments View Loader
async function loadAppointments() {
  const apts = await apiFetch("/appointments");
  currentState.appointments = apts;
  const tbody = document.getElementById("appointments-tbody");
  tbody.innerHTML = "";

  apts.forEach((apt, idx) => {
    const veh = apt.vehicle;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td><strong style="color: #38bdf8;">${veh ? veh.license_plate : 'N/A'}</strong></td>
      <td>${veh ? `${veh.brand} ${veh.model}` : 'N/A'}</td>
      <td>${new Date(apt.appointment_date).toLocaleString('vi-VN')}</td>
      <td>${apt.notes || 'Không có ghi chú'}</td>
      <td><span class="status-pill ${apt.status}">${formatStatus(apt.status)}</span></td>
      <td>
        <button class="btn btn-ai btn-sm" onclick="runAIHistorySummary(${apt.vehicle_id})"><i class="fa-solid fa-sparkles"></i> AI Tóm Tắt Lịch Sử</button>
        <button class="btn btn-primary btn-sm" onclick="convertAptToRO(${apt.id}, ${apt.vehicle_id})"><i class="fa-solid fa-car-wrench"></i> Tiếp Nhận Sửa</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  await populateVehicleDropdowns();
}

// 3. Repair Orders View Loader
async function loadRepairOrders() {
  const orders = await apiFetch("/repair-orders");
  currentState.repairOrders = orders;
  const tbody = document.getElementById("repair-orders-tbody");
  tbody.innerHTML = "";

  orders.forEach(ro => {
    const veh = ro.vehicle;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${ro.code}</strong></td>
      <td><strong style="color: #38bdf8;">${veh ? veh.license_plate : 'N/A'}</strong></td>
      <td style="max-width: 250px;">
        <div style="font-size: 0.85rem; color: var(--text-muted);">Symptom: ${ro.initial_symptoms || 'Chưa ghi nhận'}</div>
        <div style="font-size: 0.85rem; color: #cbd5e1;">Diag: ${ro.technical_diagnosis || 'Đang chẩn đoán'}</div>
      </td>
      <td><span class="status-pill ${ro.status}">${formatStatus(ro.status)}</span></td>
      <td style="color: #34d399; font-weight: 600;">${ro.final_cost.toLocaleString()} VNĐ</td>
      <td>
        <button class="btn btn-ai btn-sm" title="Trợ Lý AI Garage (Báo giá, Giải thích & Hỏi đáp tự do)" onclick="runAIServiceExplainer(${ro.id})"><i class="fa-solid fa-robot"></i> Trợ Lý AI</button>
      </td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="openRODetailModal(${ro.id})"><i class="fa-solid fa-eye"></i> Chi Tiết</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  await populateVehicleDropdowns();
}

// 4. Customers Loader
async function loadCustomersAndVehicles() {
  const customers = await apiFetch("/customers");
  currentState.customers = customers;
  const tbody = document.getElementById("customers-tbody");
  tbody.innerHTML = "";

  customers.forEach(cust => {
    const vehsStr = cust.vehicles.map(v => `<span style="background: rgba(6,182,212,0.15); padding: 2px 6px; border-radius: 4px; color: #22d3ee; margin-right: 4px;">${v.license_plate} (${v.brand} ${v.model})</span>`).join("");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${cust.full_name}</strong></td>
      <td>${cust.phone}</td>
      <td>${cust.address || 'N/A'}</td>
      <td>${vehsStr || 'Chưa có xe'}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="alert('Đã chọn khách hàng ${cust.full_name}')"><i class="fa-solid fa-pen"></i> Sửa</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 5. Inventory & Services Loader
async function loadInventory() {
  const services = await apiFetch("/services");
  const parts = await apiFetch("/parts");
  currentState.services = services;
  currentState.parts = parts;

  // Services tbody
  const srvTbody = document.getElementById("services-tbody");
  srvTbody.innerHTML = "";
  services.forEach(s => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${s.code}</code></td>
      <td><strong>${s.name}</strong></td>
      <td style="color: #34d399;">${s.labor_cost.toLocaleString()} VNĐ</td>
    `;
    srvTbody.appendChild(tr);
  });

  // Parts tbody
  const partsTbody = document.getElementById("parts-tbody");
  partsTbody.innerHTML = "";
  parts.forEach(p => {
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

// 6. Invoices Loader
async function loadInvoices() {
  const invoices = await apiFetch("/invoices");
  currentState.invoices = invoices;
  const tbody = document.getElementById("invoices-tbody");
  tbody.innerHTML = "";

  invoices.forEach(inv => {
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

// AI Functions Implementation
// AI Assistant Unified Engine Functions
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

async function openAIAssistantModal(title, initialQuestion, repairOrderId = null, vehicleId = null) {
  currentState.activeAIContext = { repair_order_id: repairOrderId, vehicle_id: vehicleId };

  const questionInput = document.getElementById("modal-ai-question-input");
  if (questionInput) questionInput.value = initialQuestion || "";

  showAIModal(title || "Trợ Lý AI Garage VTV", "⏳ Trợ lý AI đang xử lý câu hỏi của bạn...");

  try {
    const q = initialQuestion || "Hãy tư vấn các dịch vụ xe và lập báo giá nháp dự kiến";
    const res = await askAIAssistant(q, repairOrderId, vehicleId);
    showAIModal(title || "Trợ Lý AI Garage VTV", res.output, res.model_used);
  } catch (err) {
    showAIModal("Lỗi AI Assistant Engine", `❌ ${err.message}`);
  }
}

async function runAIHistorySummary(vehicleId) {
  await openAIAssistantModal(
    "AI Tóm Tắt Lịch Sử Xe & Cảnh Báo Kỹ Thuật",
    "Tóm tắt lịch sử sửa chữa và các lưu ý kỹ thuật cho xe này",
    null,
    vehicleId
  );
}

async function runAIServiceExplainer(repairOrderId) {
  await openAIAssistantModal(
    "Trợ Lý AI Garage - Báo Giá & Giải Thích Dịch Vụ",
    "Giải thích bằng ngôn ngữ dễ hiểu cho khách hàng về các hạng mục sửa chữa",
    repairOrderId
  );
}

async function runAIDraftQuotation(repairOrderId) {
  await openAIAssistantModal(
    "Trợ Lý AI Garage - Báo Giá & Giải Thích Dịch Vụ",
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

async function submitModalAIQuestion() {
  const input = document.getElementById("modal-ai-question-input");
  if (!input || !input.value.trim()) return;

  const question = input.value.trim();
  const ctx = currentState.activeAIContext || {};
  const outputBox = document.getElementById("modal-ai-body");

  if (outputBox) outputBox.textContent = `⏳ Đang gửi câu hỏi: "${question}" đến Trợ Lý AI...`;

  try {
    const res = await askAIAssistant(question, ctx.repair_order_id, ctx.vehicle_id);
    if (outputBox) outputBox.textContent = res.output;
    const badge = document.getElementById("modal-ai-model-badge");
    if (badge) badge.innerHTML = `<i class="fa-solid fa-microchip"></i> Engine: ${res.model_used}`;
  } catch (err) {
    if (outputBox) outputBox.textContent = `❌ Lỗi: ${err.message}`;
  }
}

// AI Sandbox / Assistant Tab Loader (View 7)
async function loadAISandboxData() {
  const orders = await apiFetch("/repair-orders");
  const select = document.getElementById("ai-sandbox-ro-select");
  if (!select) return;
  select.innerHTML = '<option value="">-- Không chọn phiếu (Đặt câu hỏi chung về xe) --</option>';
  orders.forEach(ro => {
    const opt = document.createElement("option");
    opt.value = ro.id;
    opt.textContent = `Mã phiếu ${ro.code} - Xe ${ro.vehicle ? ro.vehicle.license_plate : 'N/A'}`;
    select.appendChild(opt);
  });
}

function applyPromptTemplate() {
  const templateSelect = document.getElementById("ai-prompt-templates");
  const questionInput = document.getElementById("ai-free-question-input");
  if (templateSelect && questionInput && templateSelect.value) {
    questionInput.value = templateSelect.value;
  }
}

async function runAISandbox() {
  const roIdVal = document.getElementById("ai-sandbox-ro-select").value;
  const roId = roIdVal ? parseInt(roIdVal) : null;
  const questionInput = document.getElementById("ai-free-question-input");
  let question = questionInput ? questionInput.value.trim() : "";

  if (!question) {
    question = "Hãy tư vấn các gói bảo dưỡng và giải thích dịch vụ xe ô tô";
  }

  const container = document.getElementById("ai-sandbox-output-container");
  const output = document.getElementById("ai-sandbox-output");
  container.style.display = "block";
  output.textContent = "⏳ Trợ lý AI Engine đang xử lý câu hỏi của bạn...";

  try {
    const res = await askAIAssistant(question, roId);
    output.textContent = res.output;
  } catch (err) {
    output.textContent = `❌ Lỗi: ${err.message}`;
  }
}

// Modal Helpers
function showAIModal(title, bodyText, modelUsed = "Trợ Lý AI Garage VTV") {
  document.getElementById("modal-ai-title").innerHTML = `<i class="fa-solid fa-robot"></i> ${title}`;
  document.getElementById("modal-ai-body").textContent = bodyText;
  const badge = document.getElementById("modal-ai-model-badge");
  if (badge) badge.innerHTML = `<i class="fa-solid fa-microchip"></i> Engine: ${modelUsed}`;
  openModal("modal-ai-result");
}


function copyAIResult() {
  const text = document.getElementById("modal-ai-body").textContent;
  navigator.clipboard.writeText(text);
  alert("Đã sao chép nội dung AI vào bộ nhớ tạm!");
}

function openModal(modalId) {
  document.getElementById(modalId).classList.add("active");
}
function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

// Form Submissions
async function submitNewAppointment(e) {
  e.preventDefault();
  const vehicle_id = parseInt(document.getElementById("apt-vehicle-id").value);
  const appointment_date = new Date(document.getElementById("apt-date").value).isoformat ? new Date(document.getElementById("apt-date").value).toISOString() : document.getElementById("apt-date").value;
  const notes = document.getElementById("apt-notes").value;

  try {
    await apiFetch("/appointments", {
      method: "POST",
      body: JSON.stringify({ vehicle_id, appointment_date, notes })
    });
    closeModal("modal-new-appointment");
    await loadAppointments();
    alert("Đã tạo lịch hẹn thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

async function submitNewRO(e) {
  e.preventDefault();
  const vehicle_id = parseInt(document.getElementById("ro-vehicle-id").value);
  const mileage_at_reception = parseInt(document.getElementById("ro-mileage").value);
  const initial_symptoms = document.getElementById("ro-symptoms").value;

  try {
    await apiFetch("/repair-orders", {
      method: "POST",
      body: JSON.stringify({ vehicle_id, mileage_at_reception, initial_symptoms })
    });
    closeModal("modal-new-ro");
    await loadRepairOrders();
    alert("Đã tạo phiếu sửa chữa thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

async function submitNewCustomer(e) {
  e.preventDefault();
  const full_name = document.getElementById("cust-name").value;
  const phone = document.getElementById("cust-phone").value;
  const address = document.getElementById("cust-address").value;

  const license_plate = document.getElementById("cust-veh-plate").value;
  const brand = document.getElementById("cust-veh-brand").value;
  const model = document.getElementById("cust-veh-model").value;
  const year = parseInt(document.getElementById("cust-veh-year").value);

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
    alert("Đã thêm khách hàng và xe thành công!");
  } catch (err) {
    alert(`Lỗi: ${err.message}`);
  }
}

// Repair Order Detail Modal Handling
async function openRODetailModal(roId) {
  currentState.activeROId = roId;
  const ro = await apiFetch(`/repair-orders/${roId}`);

  document.getElementById("ro-detail-title").innerHTML = `<i class="fa-solid fa-wrench"></i> Phiếu Sửa Chữa ${ro.code}`;
  document.getElementById("ro-detail-info").innerHTML = `
    <strong>Xe:</strong> ${ro.vehicle ? ro.vehicle.license_plate : 'N/A'} (${ro.vehicle ? ro.vehicle.brand : ''} ${ro.vehicle ? ro.vehicle.model : ''}) | 
    <strong>Km nhận:</strong> ${ro.mileage_at_reception.toLocaleString()} km | 
    <strong>Trạng thái:</strong> <span class="status-pill ${ro.status}">${formatStatus(ro.status)}</span><br>
    <strong>Triệu chứng ban đầu:</strong> ${ro.initial_symptoms || 'Chưa có'}
  `;
  document.getElementById("ro-tech-diagnosis").value = ro.technical_diagnosis || "";
  document.getElementById("ro-detail-total").textContent = `${ro.final_cost.toLocaleString()} VNĐ`;

  // Render items
  renderROItems(ro.items);

  // Populate Add Item Catalog dropdowns
  await populateItemCatalogDropdown();

  openModal("modal-ro-detail");
}

function renderROItems(items) {
  const tbody = document.getElementById("ro-items-tbody");
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
  const type = document.getElementById("item-type-select").value;
  const select = document.getElementById("item-catalog-select");
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
  const type = document.getElementById("item-type-select").value;
  const catalogId = parseInt(document.getElementById("item-catalog-select").value);
  const qty = parseFloat(document.getElementById("item-qty").value);

  let payload = {
    item_type: type,
    quantity: qty,
    unit_price: 0,
    labor_cost: 0
  };

  if (type === "service") {
    const srv = currentState.services.find(s => s.id === catalogId);
    payload.service_id = srv.id;
    payload.name = srv.name;
    payload.labor_cost = srv.labor_cost;
  } else {
    const part = currentState.parts.find(p => p.id === catalogId);
    payload.part_id = part.id;
    payload.name = part.name;
    payload.unit_price = part.unit_price;
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
  const diag = document.getElementById("ro-tech-diagnosis").value;
  try {
    await apiFetch(`/repair-orders/${currentState.activeROId}`, {
      method: "PUT",
      body: JSON.stringify({ technical_diagnosis: diag, status: "in_progress" })
    });
    alert("Đã cập nhật chẩn đoán kỹ thuật!");
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
    alert(`Đã lập thành công Hóa đơn ${inv.invoice_number}!`);
  } catch (err) {
    alert(`Lỗi lập hóa đơn: ${err.message}`);
  }
}

// Payment Modal Handling
function openPaymentModal(invId, invNumber, balanceDue) {
  document.getElementById("pay-inv-id").value = invId;
  document.getElementById("pay-inv-number").value = invNumber;
  document.getElementById("pay-total-amount").value = `${balanceDue.toLocaleString()} VNĐ`;
  document.getElementById("pay-amount").value = balanceDue;
  openModal("modal-payment");
}

async function submitPayment(e) {
  e.preventDefault();
  const invoice_id = parseInt(document.getElementById("pay-inv-id").value);
  const payment_method = document.getElementById("pay-method").value;
  const amount = parseFloat(document.getElementById("pay-amount").value);

  try {
    await apiFetch("/payments", {
      method: "POST",
      body: JSON.stringify({ invoice_id, payment_method, amount })
    });
    closeModal("modal-payment");
    await loadInvoices();
    alert("Đã ghi nhận thanh toán thành công!");
  } catch (err) {
    alert(`Lỗi thanh toán: ${err.message}`);
  }
}

// Helpers
async function populateVehicleDropdowns() {
  const vehicles = await apiFetch("/vehicles");
  currentState.vehicles = vehicles;

  ["apt-vehicle-id", "ro-vehicle-id"].forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = "";
    vehicles.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = `${v.license_plate} (${v.brand} ${v.model})`;
      select.appendChild(opt);
    });
  });
}

function formatStatus(status) {
  const map = {
    pending: "Chờ xử lý",
    confirmed: "Đã xác nhận",
    received: "Tiếp nhận",
    diagnosing: "Chẩn đoán",
    quoted: "Đã báo giá",
    approved: "Khách duyệt",
    in_progress: "Đang sửa chữa",
    finished: "Hoàn thành",
    invoiced: "Đã lập hóa đơn",
    unpaid: "Chưa thanh toán",
    partial: "Thanh toán 1 phần",
    paid: "Đã thanh toán"
  };
  return map[status] || status;
}
