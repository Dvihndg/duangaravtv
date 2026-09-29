"""Demo catalog for local/Vercel preview environments.

Only missing codes are inserted; existing production records are preserved.
"""
from sqlalchemy.orm import Session
from backend.app.models import Service, Part

DEMO_SERVICES = [
    ("DV-001", "Bảo dưỡng định kỳ 5.000 km", "Bảo dưỡng", 450000, 60),
    ("DV-002", "Chẩn đoán lỗi động cơ Scan OBD-II", "Chẩn đoán", 300000, 45),
    ("DV-003", "Thay dầu nhớt & lọc nhớt động cơ", "Bảo dưỡng", 150000, 30),
    ("DV-004", "Bảo dưỡng định kỳ 10.000 km", "Bảo dưỡng", 750000, 120),
    ("DV-005", "Kiểm tra và sửa chữa hệ thống phanh", "Gầm & Phanh", 350000, 90),
    ("DV-006", "Cân chỉnh góc đặt bánh xe 3D", "Lốp & Gầm", 500000, 60),
    ("DV-007", "Vệ sinh kim phun và họng ga", "Động cơ", 450000, 75),
    ("DV-008", "Bảo dưỡng hệ thống điều hòa", "Điện lạnh", 650000, 120),
    ("DV-009", "Thay ắc quy và kiểm tra hệ thống sạc", "Điện ô tô", 200000, 45),
    ("DV-010", "Đồng sơn chi tiết thân vỏ", "Đồng sơn", 1800000, 480),
    ("DV-011", "Kiểm tra gầm và chạy thử", "Chẩn đoán", 150000, 30),
    ("DV-012", "Vệ sinh nội thất cao cấp", "Chăm sóc xe", 900000, 180),
    ("CB-DV-001", "Combo Thay dầu tiêu chuẩn (Dầu 5W-30 + lọc nhớt)", "Combo dịch vụ", 1050000, 45),
    ("CB-DV-002", "Combo Bảo dưỡng 10.000 km (dầu + lọc dầu + lọc gió)", "Combo dịch vụ", 1450000, 150),
    ("CB-DV-003", "Combo An toàn phanh (kiểm tra + má phanh trước)", "Combo dịch vụ", 1650000, 120),
    ("CB-DV-004", "Combo Điều hòa mát sâu (vệ sinh + nạp gas kiểm tra)", "Combo dịch vụ", 950000, 150),
    ("CB-DV-005", "Combo Chăm sóc xe cơ bản (nội thất + ngoại thất)", "Combo dịch vụ", 1800000, 240),
    ("CB-DV-006", "Combo Sẵn sàng đường dài (dầu + phanh + lốp + kiểm tra gầm)", "Combo dịch vụ", 2450000, 180),
]

DEMO_PARTS = [
    ("PT-001", "Dầu nhớt Fully Synthetic 5W-30 4L", "Motul", "Dầu nhớt", "Can", 850000, 650000, 45, 10),
    ("PT-002", "Lọc nhớt Toyota Camry/Corolla", "Toyota", "Lọc", "Cái", 180000, 120000, 30, 5),
    ("PT-003", "Má phanh trước Honda CR-V bộ 4 miếng", "Brembo", "Phanh", "Bộ", 1250000, 850000, 15, 4),
    ("PT-004", "Lọc gió động cơ Mazda 3/CX-5", "Mazda", "Lọc", "Cái", 420000, 280000, 18, 5),
    ("PT-005", "Lọc gió điều hòa Carbon", "Denso", "Điều hòa", "Cái", 450000, 300000, 8, 5),
    ("PT-006", "Bugi Iridium Toyota/Honda", "NGK", "Động cơ", "Cái", 280000, 170000, 24, 8),
    ("PT-007", "Ắc quy 12V 60Ah", "GS", "Điện ô tô", "Bình", 1850000, 1450000, 6, 3),
    ("PT-008", "Dây curoa tổng hợp", "Gates", "Động cơ", "Sợi", 650000, 420000, 12, 4),
    ("PT-009", "Nước làm mát 4L", "Liqui Moly", "Dung dịch", "Can", 320000, 210000, 20, 5),
    ("PT-010", "Dầu phanh DOT 4 1L", "BOSCH", "Phanh", "Chai", 240000, 150000, 25, 6),
    ("PT-011", "Lốp Michelin Primacy 4 215/55R17", "Michelin", "Lốp", "Cái", 3150000, 2600000, 4, 4),
    ("PT-012", "Lốp Bridgestone Turanza 205/55R16", "Bridgestone", "Lốp", "Cái", 2450000, 1980000, 7, 4),
    ("PT-013", "Rô-tuyn lái ngoài", "555", "Gầm", "Cái", 550000, 350000, 9, 3),
    ("PT-014", "Phuộc trước Toyota Vios", "KYB", "Gầm", "Cái", 1450000, 1050000, 5, 2),
    ("PT-015", "Nước rửa kính 1L", "Garage VTV", "Dung dịch", "Chai", 85000, 45000, 60, 10),
    ("PT-016", "Dung dịch vệ sinh kim phun", "Liqui Moly", "Động cơ", "Chai", 350000, 220000, 14, 5),
    ("PT-017", "Lọc nhiên liệu diesel", "MANN", "Lọc", "Cái", 480000, 310000, 3, 5),
    ("PT-018", "Mô-bin đánh lửa Toyota", "Denso", "Điện động cơ", "Cái", 980000, 720000, 6, 2),
    ("PT-019", "Gas lạnh R134a nạp bổ sung", "Denso", "Điều hòa", "Lon", 280000, 170000, 11, 4),
    ("PT-020", "Khăn lau microfiber cao cấp", "Garage VTV", "Chăm sóc xe", "Cái", 95000, 50000, 80, 15),
    ("CB-KHO-001", "Combo kho: Dầu 5W-30 + lọc nhớt", "Garage VTV", "Combo đóng gói", "Combo", 1050000, 770000, 8, 2),
    ("CB-KHO-002", "Combo kho: Bộ bảo dưỡng 10.000 km", "Garage VTV", "Combo đóng gói", "Combo", 1450000, 1080000, 5, 2),
    ("CB-KHO-003", "Combo kho: Má phanh trước + dầu phanh DOT 4", "Garage VTV", "Combo đóng gói", "Combo", 1650000, 1040000, 3, 2),
    ("CB-KHO-004", "Combo kho: Vệ sinh điều hòa + gas R134a", "Garage VTV", "Combo đóng gói", "Combo", 950000, 590000, 6, 2),
    ("CB-KHO-005", "Combo kho: Chăm sóc nội thất & ngoại thất", "Garage VTV", "Combo đóng gói", "Combo", 1800000, 980000, 4, 2),
    ("CB-KHO-006", "Combo kho: Sẵn sàng đường dài", "Garage VTV", "Combo đóng gói", "Combo", 2450000, 1740000, 2, 2),
]


def ensure_demo_catalog(db: Session) -> None:
    existing_services = {row.code for row in db.query(Service.code).all()}
    for code, name, category, labor_cost, duration in DEMO_SERVICES:
        if code not in existing_services:
            db.add(Service(code=code, name=name, category=category, labor_cost=labor_cost, estimated_duration=duration, estimated_hours=duration / 60))
    db.commit()

    existing_parts = {row.code for row in db.query(Part.code).all()}
    for code, name, brand, category, unit, sell, cost, stock, minimum in DEMO_PARTS:
        if code not in existing_parts:
            db.add(Part(code=code, name=name, brand=brand, category=category, unit=unit, unit_price=sell, cost_price=cost, stock_quantity=stock, min_stock_alert=minimum, supplier="Nhà cung cấp demo VTV", location="Kho A"))
    db.commit()
