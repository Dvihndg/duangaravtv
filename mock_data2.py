import sqlite3
import datetime
from datetime import timedelta
import random

conn = sqlite3.connect('backend/garage.db')
c = conn.cursor()
now = datetime.datetime.now()

customer_requests = [
    ("REQ-001", "Trần D", "0909090909", "d@example.com", "Hà Nội", "30H-111.11", "Mazda", "CX-5", 2021, 15000, "Bảo dưỡng", "Bảo dưỡng xe", "2026-09-15", "10:00", "", "pending", "", None, None, None, now.isoformat(), now.isoformat(), "web", None, None, None, None),
    ("REQ-002", "Lý E", "0808080808", "e@example.com", "Hà Nội", "29K-222.22", "Kia", "Cerato", 2020, 25000, "Sửa chữa", "Lỗi động cơ", "2026-09-15", "14:00", "", "approved", "", None, None, None, (now - timedelta(hours=1)).isoformat(), (now - timedelta(hours=1)).isoformat(), "app", None, None, None, None)
]

c.executemany("""INSERT OR IGNORE INTO customer_requests 
              (request_code, full_name, phone, email, address, license_plate, vehicle_brand, vehicle_model, 
              manufacture_year, current_mileage, service_type, description, preferred_date, preferred_time, 
              note, status, admin_note, assigned_employee_id, customer_id, vehicle_id, created_at, updated_at, 
              source, appointment_id, reviewed_by_id, reviewed_at, converted_at) 
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
              customer_requests)

conn.commit()
conn.close()
print("Mock data 2 added successfully.")
