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

        # 4. Create Customers & Vehicles (5 khách hàng, 7 ô tô)
        c1 = Customer(full_name="Nguyễn Hoàng Nam", phone="0988123456", email="nam.nguyen@gmail.com", address="123 Lê Duẩn, Quận 1, TP.HCM")
        c2 = Customer(full_name="Đặng Thị Minh Anh", phone="0977654321", email="minhanh@yahoo.com", address="456 Nguyễn Thị Minh Khai, Quận 3, TP.HCM")
        c3 = Customer(full_name="Trần Quốc Tuấn", phone="0912345678", email="tuantran@outlook.com", address="789 Nguyễn Văn Linh, Quận 7, TP.HCM")
        c4 = Customer(full_name="Lê Thị Mai Hương", phone="0933888999", email="maihuong@gmail.com", address="12 Phạm Văn Đồng, Bình Thạnh, TP.HCM")
        c5 = Customer(full_name="Vũ Hoàng Long", phone="0909112233", email="longvu@garage.vn", address="88 Võ Văn Kiệt, Quận 5, TP.HCM")
        db.add_all([c1, c2, c3, c4, c5])
        db.commit()

        v1 = Vehicle(license_plate="51H-888.99", brand="Toyota", model="Camry 2.5Q", year=2021, color="Đen", current_mileage=45000, customer_id=c1.id)
        v2 = Vehicle(license_plate="30A-666.88", brand="Honda", model="Civic RS", year=2022, color="Trắng", current_mileage=28000, customer_id=c2.id)
        v3 = Vehicle(license_plate="51K-123.45", brand="BMW", model="X5 xDrive40i", year=2020, color="Xanh cavansite", current_mileage=62000, customer_id=c1.id)
        v4 = Vehicle(license_plate="51G-999.99", brand="Mercedes-Benz", model="E300 AMG", year=2022, color="Đỏ Hyacinth", current_mileage=35000, customer_id=c3.id)
        v5 = Vehicle(license_plate="30H-456.78", brand="VinFast", model="VF8 Plus", year=2023, color="Xám VinFast", current_mileage=18000, customer_id=c4.id)
        v6 = Vehicle(license_plate="51F-333.22", brand="Hyundai", model="Tucson 2.0 Special", year=2019, color="Bạc", current_mileage=72000, customer_id=c5.id)
        v7 = Vehicle(license_plate="60A-777.11", brand="Ford", model="Ranger Wildtrak 2.0L", year=2021, color="Vàng cam", current_mileage=55000, customer_id=c3.id)
        db.add_all([v1, v2, v3, v4, v5, v6, v7])
        db.commit()

        # 5. Create Completed Repair Orders (History)
        ro_old1 = RepairOrder(
            code="RO-20260115-001",
            vehicle_id=v1.id,
            technician_id=tech.id,
            receptionist_id=receptionist.id,
            mileage_at_reception=40000,
            initial_symptoms="Xe báo đèn nhắc bảo dưỡng mốc 40.000 km",
            technical_diagnosis="Động cơ hoạt động tốt, đã thay dầu nhờn và lọc dầu mới.",
            status=RepairOrderStatus.FINISHED,
            estimated_cost=1080000.0,
            final_cost=1080000.0,
            ai_history_summary="Lịch sử: Xe Toyota Camry mốc 40,000 km thay dầu Castrol 5W-30 & lọc dầu chính hãng.",
            completed_at=datetime.utcnow() - timedelta(days=40)
        )
        ro_old2 = RepairOrder(
            code="RO-20260210-002",
            vehicle_id=v4.id,
            technician_id=tech2.id,
            receptionist_id=receptionist.id,
            mileage_at_reception=30000,
            initial_symptoms="Vệ sinh phanh & thay gạt mưa Mercedes",
            technical_diagnosis="Phanh bẩn gây rít nhẹ, gạt mưa mòn cao su.",
            status=RepairOrderStatus.FINISHED,
            estimated_cost=680000.0,
            final_cost=680000.0,
            ai_history_summary="Lịch sử: Bảo dưỡng phanh Mercedes E300 và thay gạt mưa Bosch.",
            completed_at=datetime.utcnow() - timedelta(days=15)
        )
        db.add_all([ro_old1, ro_old2])
        db.commit()

        # Items for ro_old1
        db.add_all([
            RepairOrderItem(repair_order_id=ro_old1.id, item_type=RepairOrderItemType.SERVICE, service_id=services[0].id, name=services[0].name, quantity=1, unit_price=0, labor_cost=150000.0, total_price=150000.0),
            RepairOrderItem(repair_order_id=ro_old1.id, item_type=RepairOrderItemType.PART, part_id=parts[0].id, name=parts[0].name, quantity=1, unit_price=750000.0, labor_cost=0, total_price=750000.0),
            RepairOrderItem(repair_order_id=ro_old1.id, item_type=RepairOrderItemType.PART, part_id=parts[1].id, name=parts[1].name, quantity=1, unit_price=180000.0, labor_cost=0, total_price=180000.0),
        ])
        # Items for ro_old2
        db.add_all([
            RepairOrderItem(repair_order_id=ro_old2.id, item_type=RepairOrderItemType.SERVICE, service_id=services[1].id, name=services[1].name, quantity=1, unit_price=0, labor_cost=300000.0, total_price=300000.0),
            RepairOrderItem(repair_order_id=ro_old2.id, item_type=RepairOrderItemType.PART, part_id=parts[7].id, name=parts[7].name, quantity=1, unit_price=380000.0, labor_cost=0, total_price=380000.0),
        ])
        db.commit()

        # Invoices and Payments for finished repair orders
        inv1 = Invoice(
            invoice_number="INV-20260115-001",
            repair_order_id=ro_old1.id,
            subtotal=1080000.0,
            tax_amount=86400.0,
            total_amount=1166400.0,
            paid_amount=1166400.0,
            balance_due=0.0,
            status=InvoiceStatus.PAID
        )
        inv2 = Invoice(
            invoice_number="INV-20260210-002",
            repair_order_id=ro_old2.id,
            subtotal=680000.0,
            tax_amount=54400.0,
            total_amount=734400.0,
            paid_amount=734400.0,
            balance_due=0.0,
            status=InvoiceStatus.PAID
        )
        db.add_all([inv1, inv2])
        db.commit()

        db.add_all([
            Payment(invoice_id=inv1.id, payment_method=PaymentMethod.BANK_TRANSFER, amount=1166400.0, cashier_id=cashier.id, transaction_reference="PAY-001 (Chuyển khoản VCB)"),
            Payment(invoice_id=inv2.id, payment_method=PaymentMethod.CASH, amount=734400.0, cashier_id=cashier.id, transaction_reference="PAY-002 (Tiền mặt quầy)"),
        ])
        db.commit()


        # 6. Create Active Repair Orders (IN_PROGRESS & DRAFT)
        ro_active1 = RepairOrder(
            code="RO-20260828-001",
            vehicle_id=v1.id,
            technician_id=tech.id,
            receptionist_id=receptionist.id,
            mileage_at_reception=45000,
            initial_symptoms="Xe có tiếng kêu lách cách khi phanh gắt và vô lăng hơi rung khi chạy tốc độ cao",
            technical_diagnosis="Má phanh trước bị mòn gờ, lốp trước lệch thước lái khoảng 1.5 độ cần rà đĩa & căn chỉnh laser.",
            status=RepairOrderStatus.IN_PROGRESS,
            estimated_cost=2106000.0,
            final_cost=1950000.0,
            ai_history_summary="[DeepSeek Pro V4 AI]: Lần bảo dưỡng trước ở mốc 40,000 km đã thay dầu Castrol và lọc dầu. Lần này phát hiện mòn gờ phanh và lệch thước lái.",
            ai_service_explanation="[DeepSeek Pro V4 AI]: Kính gửi anh Nam: Garage tiến hành rà lại đĩa phanh, thay má phanh Brembo cao cấp và căn chỉnh góc đặt bánh xe 3D Laser.",
            ai_draft_quotation_notes="[DeepSeek Pro V4 AI]: Báo giá nháp: Phanh Brembo (1.200.000đ) + Căn thước lái (450.000đ) + Công bảo dưỡng phanh (300.000đ). VAT 8%: 156.000đ. Tổng: 2.106.000đ"
        )

        ro_active2 = RepairOrder(
            code="RO-20260828-002",
            vehicle_id=v5.id,
            technician_id=tech2.id,
            receptionist_id=receptionist.id,
            mileage_at_reception=18000,
            initial_symptoms="Xe điện VinFast VF8 vệ sinh dàn lạnh và kiểm tra ắc quy phụ 12V",
            technical_diagnosis="Dàn lạnh tích tụ bụi bẩn sinh học, ắc quy 12V điện áp ổn định.",
            status=RepairOrderStatus.IN_PROGRESS,
            estimated_cost=540000.0,
            final_cost=500000.0,
            ai_history_summary="[DeepSeek Pro V4 AI]: Xe VinFast VF8 mới bảo dưỡng lần đầu tại garage.",
            ai_service_explanation="[DeepSeek Pro V4 AI]: Tiến hành vệ sinh nội soi giàn lạnh bằng dung dịch sinh học và quét lỗi máy chẩn đoán.",
            ai_draft_quotation_notes="[DeepSeek Pro V4 AI]: Báo giá nháp: Công vệ sinh HVAC 500,000đ. VAT 8%: 40,000đ. Tổng: 540,000đ"
        )

        ro_draft = RepairOrder(
            code="RO-20260828-003",
            vehicle_id=v6.id,
            technician_id=tech.id,
            receptionist_id=receptionist.id,
            mileage_at_reception=72000,
            initial_symptoms="Xe Hyundai Tucson điều hòa thổi gió nóng, không mát khi dừng đèn đỏ",
            technical_diagnosis="Đang kiểm tra áp suất lốc lạnh và lượng gas R134a",
            status=RepairOrderStatus.DIAGNOSING,
            estimated_cost=0.0,
            final_cost=0.0
        )

        db.add_all([ro_active1, ro_active2, ro_draft])
        db.commit()

        # Items for ro_active1
        db.add_all([
            RepairOrderItem(repair_order_id=ro_active1.id, item_type=RepairOrderItemType.SERVICE, service_id=services[1].id, name=services[1].name, quantity=1, unit_price=0, labor_cost=300000.0, total_price=300000.0),
            RepairOrderItem(repair_order_id=ro_active1.id, item_type=RepairOrderItemType.PART, part_id=parts[2].id, name=parts[2].name, quantity=1, unit_price=1200000.0, labor_cost=0, total_price=1200000.0),
            RepairOrderItem(repair_order_id=ro_active1.id, item_type=RepairOrderItemType.SERVICE, service_id=services[2].id, name=services[2].name, quantity=1, unit_price=0, labor_cost=450000.0, total_price=450000.0),
        ])
        # Items for ro_active2
        db.add_all([
            RepairOrderItem(repair_order_id=ro_active2.id, item_type=RepairOrderItemType.SERVICE, service_id=services[4].id, name=services[4].name, quantity=1, unit_price=0, labor_cost=500000.0, total_price=500000.0),
        ])
        db.commit()

        # 7. Create Appointments (4 lịch hẹn)
        apt1 = Appointment(
            vehicle_id=v2.id,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            notes="Khách đăng ký bảo dưỡng mốc 30.000 km và thay bugi NGK",
            status=AppointmentStatus.PENDING,
            assigned_technician_id=tech.id
        )
        apt2 = Appointment(
            vehicle_id=v3.id,
            appointment_date=datetime.utcnow() + timedelta(days=2),
            notes="BMW X5 kiểm tra hệ thống treo khí nén & thay lọc gió động cơ Bosch",
            status=AppointmentStatus.CONFIRMED,
            assigned_technician_id=tech2.id
        )
        apt3 = Appointment(
            vehicle_id=v7.id,
            appointment_date=datetime.utcnow() + timedelta(days=3),
            notes="Ford Ranger bảo dưỡng định kỳ & súc rửa kim phun nhiên liệu",
            status=AppointmentStatus.CONFIRMED,
            assigned_technician_id=tech.id
        )
        apt4 = Appointment(
            vehicle_id=v4.id,
            appointment_date=datetime.utcnow() - timedelta(days=15),
            notes="Mercedes E300 bảo dưỡng phanh định kỳ",
            status=AppointmentStatus.COMPLETED,
            assigned_technician_id=tech2.id
        )
        db.add_all([apt1, apt2, apt3, apt4])
        db.commit()

        print("[OK] Đã nạp thành công toàn bộ dữ liệu mẫu vô cùng phong phú cho Garage!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Lỗi nạp dữ liệu mẫu: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("[START] Đang khởi tạo dữ liệu mẫu cho Hệ thống Quản lý Garage...")
    seed_database()
