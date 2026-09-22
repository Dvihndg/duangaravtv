import sqlite3
import datetime
from datetime import timedelta
import random

conn = sqlite3.connect('backend/garage.db')
c = conn.cursor()

now = datetime.datetime.now()

# Customers
customers = [
    ("KH-001", "Nguyễn Văn A", "0901234567", "a@example.com", "Hà Nội", "VIP", "active"),
    ("KH-002", "Trần Thị B", "0912345678", "b@example.com", "Hà Nội", "Regular", "active"),
    ("KH-003", "Lê Văn C", "0987654321", "c@example.com", "Hà Nội", "New", "active")
]
c.executemany("INSERT OR IGNORE INTO customers (customer_code, full_name, phone, email, address, notes, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              [(k[0], k[1], k[2], k[3], k[4], k[5], k[6], (now - timedelta(days=random.randint(1, 30))).isoformat()) for k in customers])

# Vehicles
vehicles = [
    ("30A-123.45", "Toyota", "Camry", 2018, "Trắng", "VIN123", "ENG123", 45000, "Xăng", "Tự động", "", 1),
    ("29C-987.65", "Ford", "Ranger", 2020, "Cam", "VIN456", "ENG456", 20000, "Dầu", "Số sàn", "", 2),
    ("30F-555.55", "Honda", "CR-V", 2019, "Đen", "VIN789", "ENG789", 35000, "Xăng", "Tự động", "", 3)
]
c.executemany("INSERT OR IGNORE INTO vehicles (license_plate, brand, model, year, color, vin_number, engine_number, current_mileage, fuel_type, transmission, notes, customer_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              [(v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9], v[10], v[11], now.isoformat()) for v in vehicles])

# Appointments (Lịch hẹn hôm nay)
appointments = [
    ("AP-001", 1, 1, now.isoformat(), "08:00", "10:00", "Bảo dưỡng 4 vạn", "Thay dầu, lọc dầu", "Khách VIP", "confirmed", 1),
    ("AP-002", 2, 2, now.isoformat(), "14:00", "16:00", "Kiểm tra phanh", "Phanh kêu rít", "", "pending", 2)
]
c.executemany("INSERT OR IGNORE INTO appointments (appointment_code, customer_id, vehicle_id, appointment_date, start_time, end_time, service_type, description, notes, status, assigned_technician_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              [(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], now.isoformat()) for a in appointments])

# Repair Orders (Xe đang sửa)
repair_orders = [
    ("RO-001", 1, 1, 1, 1, 1, 1, 45000, 45000, 45000, "Bảo dưỡng", "Bảo dưỡng", "Bảo dưỡng", "", "", "", "in_progress", 500000, 0, (now + timedelta(hours=2)).isoformat(), None, "", "", "", now.isoformat(), None),
    ("RO-002", 2, 2, 2, 2, 2, 2, 20000, 20000, 20000, "Phanh", "Phanh", "Phanh", "", "", "", "completed", 1500000, 1500000, now.isoformat(), now.isoformat(), "", "", "", (now - timedelta(days=2)).isoformat(), (now - timedelta(days=1)).isoformat())
]
c.executemany("""INSERT OR IGNORE INTO repair_orders 
              (code, customer_id, vehicle_id, appointment_id, reception_id, technician_id, receptionist_id, 
              mileage_in, mileage_out, mileage_at_reception, customer_complaint, initial_symptoms, 
              technical_diagnosis, inspection_notes, internal_notes, customer_notes, status, 
              estimated_cost, final_cost, estimated_completion, actual_completion, ai_history_summary, 
              ai_service_explanation, ai_draft_quotation_notes, created_at, completed_at) 
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
              repair_orders)

# Invoices (Doanh thu tháng, 6 tháng gần nhất)
invoices = []
for i in range(1, 7):
    date = (now - timedelta(days=30*i - 15)).isoformat()
    amt = random.randint(10000000, 50000000)
    invoices.append((f"INV-10{i}", 100+i, 2, 2, date, date, amt, 0, 0, 0, amt, amt, amt, 0, 0, "paid", date, "", date, date))

# Current month invoices
invoices.append(("INV-001", 1, 1, 1, (now - timedelta(days=1)).isoformat(), now.isoformat(), 150000000, 0, 0, 0, 150000000, 150000000, 150000000, 0, 0, "paid", (now - timedelta(days=1)).isoformat(), "", (now - timedelta(days=1)).isoformat(), (now - timedelta(days=1)).isoformat()))
invoices.append(("INV-002", 2, 2, 2, (now - timedelta(days=5)).isoformat(), now.isoformat(), 2500000, 0, 0, 0, 2500000, 2500000, 2500000, 0, 0, "paid", (now - timedelta(days=5)).isoformat(), "", (now - timedelta(days=5)).isoformat(), (now - timedelta(days=5)).isoformat()))

c.executemany("""INSERT OR IGNORE INTO invoices 
              (invoice_number, repair_order_id, customer_id, vehicle_id, invoice_date, due_date, 
              subtotal, discount_amount, tax_amount, vat, total_amount, total, paid_amount, balance_due, remaining_amount, 
              status, issued_date, notes, created_at, updated_at) 
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", invoices)

conn.commit()
conn.close()
print("Mock data added successfully.")
