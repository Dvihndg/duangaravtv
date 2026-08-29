import sys
from datetime import datetime, timedelta
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.app.database import SessionLocal, engine, Base

from backend.app.models import (
    User, UserRole, Customer, Vehicle, Service, Part,
    Appointment, AppointmentStatus, RepairOrder, RepairOrderStatus,
    RepairOrderItem, RepairOrderItemType, Invoice, InvoiceStatus, Payment, PaymentMethod
)
from backend.app.auth import get_password_hash

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 1. Create Users for 4 Roles
        manager = User(
            username="admin",
            email="admin@garage.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Nguyễn Văn Quản Lý",
            role=UserRole.MANAGER,
            phone="0901111111"
        )
        receptionist = User(
            username="letan",
            email="letan@garage.com",
            hashed_password=get_password_hash("letan123"),
            full_name="Trần Thị Lễ Tân",
            role=UserRole.RECEPTIONIST,
            phone="0902222222"
        )
        tech = User(
            username="kythuat",
            email="kythuat@garage.com",
            hashed_password=get_password_hash("tech123"),
            full_name="Lê Hoàng Kỹ Thuật",
            role=UserRole.TECHNICIAN,
            phone="0903333333"
        )
        tech2 = User(
            username="kythuat2",
            email="kythuat2@garage.com",
            hashed_password=get_password_hash("tech456"),
            full_name="Phạm Văn Minh (KTV Điện - Máy)",
            role=UserRole.TECHNICIAN,
            phone="0905555555"
        )
        cashier = User(
            username="thungan",
            email="thungan@garage.com",
            hashed_password=get_password_hash("cashier123"),
            full_name="Phạm Thu Ngân",
            role=UserRole.CASHIER,
            phone="0904444444"
        )
        db.add_all([manager, receptionist, tech, tech2, cashier])
        db.commit()

        # 2. Create Services Catalog (10 hạng mục)
        services = [
            Service(code="SER-001", name="Thay dầu động cơ & Lọc dầu", category="Bảo dưỡng", description="Thay dầu nhờn tổng hợp cao cấp Castrol/Motul và lọc dầu động cơ chính hãng", labor_cost=150000.0, estimated_hours=0.5),
            Service(code="SER-002", name="Bảo dưỡng & Căn chỉnh hệ thống Phanh", category="Bảo dưỡng", description="Vệ sinh đĩa phanh, rà guốc phanh và bổ sung dầu phanh DOT4", labor_cost=300000.0, estimated_hours=1.5),
            Service(code="SER-003", name="Cân bằng động & Cân chỉnh thước lái Laser", category="Lốp & Khung gầm", description="Đo đọc góc đặt bánh xe bằng hệ thống 3D Laser hiện đại", labor_cost=450000.0, estimated_hours=1.0),
            Service(code="SER-004", name="Súc rửa kim phun & Cổ hút ga sinh học", category="Động cơ", description="Tẩy rửa muội than carbon trong buồng đốt và kim phun điện tử", labor_cost=350000.0, estimated_hours=1.0),
            Service(code="SER-005", name="Kiểm tra & Vệ sinh điều hòa (HVAC)", category="Điện & Điều hòa", description="Vệ sinh giàn lạnh bằng nội soi sinh học, bổ sung gas R134a", labor_cost=500000.0, estimated_hours=2.0),
            Service(code="SER-006", name="Đại tu & Thay thế bộ Ly hợp / Hộp số", category="Hộp số", description="Kiểm tra lá côn, mâm ép, bi T và thay dầu hộp số tự động/cơ", labor_cost=1500000.0, estimated_hours=5.0),
            Service(code="SER-007", name="Vệ sinh gầm xe & Phủ bóng Ceramic bảo vệ sơn", category="Chăm sóc xe", description="Rửa gầm áp lực cao, tẩy ố kính và phủ 2 lớp Ceramic cao cấp", labor_cost=1200000.0, estimated_hours=4.0),
            Service(code="SER-008", name="Chẩn đoán & Xóa lỗi đọc chuẩn OBD-II", category="Điện & Điều hòa", description="Quét toàn bộ cảm biến ECU, xóa mã lỗi hư hỏng điện tử", labor_cost=200000.0, estimated_hours=0.5),
            Service(code="SER-009", name="Thay bình ắc quy & Kiểm tra máy phát", category="Điện & Điều hòa", description="Đo điện áp sạc, thay lắp bình ắc quy khô chính hãng GS/Varta", labor_cost=100000.0, estimated_hours=0.5),
            Service(code="SER-010", name="Bảo dưỡng tổng thể mốc 80.000 km", category="Bảo dưỡng", description="Kiểm tra 45 hạng mục an toàn, thay dung dịch mát, bugi & lọc khí", labor_cost=800000.0, estimated_hours=3.5),
        ]
        db.add_all(services)
        db.commit()

        # 3. Create Spare Parts Inventory (10 loại phụ tùng)
        parts = [
            Part(code="PAR-001", name="Dầu động cơ Castrol Edge 5W-30 (Can 4L)", brand="Castrol", unit_price=750000.0, cost_price=550000.0, stock_quantity=25, min_stock_alert=5),
            Part(code="PAR-002", name="Lọc dầu Toyota Camry/Corolla", brand="Toyota Genuine", unit_price=180000.0, cost_price=120000.0, stock_quantity=30, min_stock_alert=5),
            Part(code="PAR-003", name="Má phanh trước Honda Civic / CRV", brand="Brembo", unit_price=1200000.0, cost_price=850000.0, stock_quantity=8, min_stock_alert=3),
            Part(code="PAR-004", name="Lọc gió động cơ BMW X5 / X6", brand="Bosch", unit_price=450000.0, cost_price=300000.0, stock_quantity=4, min_stock_alert=5), # Low stock alert!
            Part(code="PAR-005", name="Bugi Iridium NGK Laser Premium", brand="NGK", unit_price=220000.0, cost_price=150000.0, stock_quantity=16, min_stock_alert=4),
            Part(code="PAR-006", name="Bình ắc quy khô GS 12V-65Ah", brand="GS Battery", unit_price=1650000.0, cost_price=1250000.0, stock_quantity=10, min_stock_alert=3),
            Part(code="PAR-007", name="Lốp xe Michelin Pilot Sport 4 (235/45R18)", brand="Michelin", unit_price=3400000.0, cost_price=2750000.0, stock_quantity=12, min_stock_alert=4),
            Part(code="PAR-008", name="Cặp gạt mưa Silicon Bosch Aerotwin", brand="Bosch", unit_price=380000.0, cost_price=240000.0, stock_quantity=2, min_stock_alert=5), # Low stock alert!
            Part(code="PAR-009", name="Dầu phanh cao cấp Motul DOT4 (1L)", brand="Motul", unit_price=250000.0, cost_price=170000.0, stock_quantity=15, min_stock_alert=4),
            Part(code="PAR-010", name="Nước làm mát động cơ Motul Inugel (5L)", brand="Motul", unit_price=420000.0, cost_price=290000.0, stock_quantity=20, min_stock_alert=5),
        ]
        db.add_all(parts)
        db.commit()

        print("[OK] Đã nạp thành công tài khoản nhân viên, danh mục dịch vụ và kho phụ tùng chuẩn!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Lỗi nạp dữ liệu mẫu: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("[START] Đang khởi tạo dữ liệu mẫu cho Hệ thống Quản lý Garage...")
    seed_database()
