import sys
from datetime import datetime, timedelta
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.app.database import SessionLocal, engine, Base
from backend.app.models import (
    User, UserRole, Customer, Vehicle, Service, Part,
    Appointment, AppointmentStatus, RepairOrder, RepairOrderStatus,
    VehicleReception, Inspection, InspectionCategory, InspectionSeverity,
    Quotation, QuotationItem, QuotationStatus,
    RepairOrderService, RepairOrderPart, RepairOrderItem, RepairOrderItemType,
    Invoice, InvoiceStatus, Payment, PaymentMethod, Setting
)
from backend.app.auth import get_password_hash

def seed_database():
    print("--- Khởi tạo CSDL Garage VTV AI Management System ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 1. USERS & 4 ROLES
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
        tech1 = User(
            username="kythuat",
            email="kythuat@garage.com",
            hashed_password=get_password_hash("tech123"),
            full_name="Lê Hoàng Kỹ Thuật (KTV Trưởng)",
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
        db.add_all([manager, receptionist, tech1, tech2, cashier])
        db.flush()

        # 2. SYSTEM SETTINGS
        settings = [
            Setting(key="VAT_RATE", value="0.10", description="Thuế suất VAT mặc định"),
            Setting(key="DEFAULT_CURRENCY", value="VND", description="Đơn vị tiền tệ chính"),
            Setting(key="GARAGE_NAME", value="Garage VTV Automotive", description="Tên thương hiệu"),
            Setting(key="HOTLINE", value="1900 6868", description="Số điện thoại tổng đài"),
            Setting(key="ADDRESS", value="Số 88 Đường Giải Phóng, Hà Nội", description="Địa chỉ xưởng")
        ]
        db.add_all(settings)

        # 3. 20+ CUSTOMERS
        viet_names = [
            "Nguyễn Văn An", "Trần Đình Trọng", "Lê Văn Hùng", "Phạm Thị Mai", "Hoàng Văn Tuấn",
            "Đặng Quốc Bảo", "Vũ Thị Hương", "Bùi Tiến Dũng", "Đỗ Quang Hải", "Hồ Ngọc Hà",
            "Dương Công Minh", "Ngô Tất Tố", "Đinh Tiên Hoàng", "Lý Thường Kiệt", "Võ Nguyên Giáp",
            "Phan Bội Châu", "Nguyễn Du", "Trương Vĩnh Ký", "Nguyễn Huệ", "Lê Lợi",
            "Trần Hưng Đạo", "Bà Trưng"
        ]
        customers = []
        for i, name in enumerate(viet_names, start=1):
            c = Customer(
                customer_code=f"CUS-2026-{i:06d}",
                full_name=name,
                phone=f"09{i:02d}123{i:03d}"[:10],
                email=f"khachhang{i}@gmail.com",
                address=f"Số {i*3} Đường CMT8, Quận {((i%12)+1)}, TP.HCM",
                status="ACTIVE"
            )
            customers.append(c)
        db.add_all(customers)
        db.flush()

        # 4. 30+ VEHICLES
        car_models = [
            ("Toyota", "Camry", 2020), ("Toyota", "Vios", 2021), ("Toyota", "Fortuner", 2019),
            ("Toyota", "Corolla Cross", 2022), ("Honda", "Civic", 2020), ("Honda", "CR-V", 2021),
            ("Honda", "City", 2022), ("Mazda", "3", 2021), ("Mazda", "CX-5", 2020),
            ("Mazda", "6", 2019), ("Ford", "Ranger", 2021), ("Ford", "Everest", 2022),
            ("Ford", "Territory", 2023), ("Hyundai", "SantaFe", 2021), ("Hyundai", "Tucson", 2020),
            ("Hyundai", "Accent", 2022), ("Hyundai", "Creta", 2023), ("Kia", "Seltos", 2021),
            ("Kia", "Sorento", 2022), ("Kia", "K3", 2021), ("Kia", "Carnival", 2022),
            ("Mitsubishi", "Xpander", 2022), ("Mitsubishi", "Outlander", 2021),
            ("Mercedes-Benz", "C200", 2020), ("Mercedes-Benz", "E300", 2021),
            ("BMW", "320i", 2020), ("BMW", "520i", 2021), ("Audi", "A4", 2019),
            ("Lexus", "RX350", 2020), ("VinFast", "VF8", 2023), ("VinFast", "Lux A2.0", 2021),
            ("Subaru", "Forester", 2022)
        ]
        vehicles = []
        for i, (brand, model, year) in enumerate(car_models, start=1):
            owner = customers[i % len(customers)]
            v = Vehicle(
                license_plate=f"51A-{i:03d}.{(i*7)%90 + 10}",
                brand=brand,
                model=model,
                year=year,
                color="Trắng" if i % 3 == 0 else ("Đen" if i % 3 == 1 else "Bạc"),
                vin_number=f"VIN{year}{brand[:2].upper()}{i:08d}",
                engine_number=f"ENG{i:08d}",
                current_mileage=15000 + (i * 3500),
                customer_id=owner.id
            )
            vehicles.append(v)
        db.add_all(vehicles)
        db.flush()

        # 5. 20+ SERVICES
        service_catalog = [
            ("SER-001", "Bảo dưỡng định kỳ cấp 1 (5,000km)", "Bảo dưỡng", 200000.0, 1.0),
            ("SER-002", "Bảo dưỡng định kỳ cấp 2 (10,000km)", "Bảo dưỡng", 350000.0, 1.5),
            ("SER-003", "Bảo dưỡng định kỳ cấp 3 (20,000km)", "Bảo dưỡng", 600000.0, 2.5),
            ("SER-004", "Bảo dưỡng định kỳ cấp 4 (40,000km)", "Bảo dưỡng", 1200000.0, 4.0),
            ("SER-005", "Thay dầu động cơ & lọc dầu", "Dầu nhờn", 150000.0, 0.5),
            ("SER-006", "Vệ sinh hệ thống thắng 4 bánh", "Phanh", 300000.0, 1.0),
            ("SER-007", "Thay má phanh trước", "Phanh", 250000.0, 1.0),
            ("SER-008", "Thay má phanh sau", "Phanh", 250000.0, 1.0),
            ("SER-009", "Láng đĩa phanh bằng máy tự động", "Phanh", 400000.0, 1.5),
            ("SER-010", "Vệ sinh họng ga & kim phun xăng điện tử", "Động cơ", 450000.0, 1.5),
            ("SER-011", "Vệ sinh buồng đốt bằng hydro", "Động cơ", 500000.0, 1.0),
            ("SER-012", "Cân bằng động & đảo lốp", "Lốp xe", 200000.0, 0.8),
            ("SER-013", "Cân chỉnh góc đặt bánh xe 3D", "Gầm lái", 600000.0, 1.5),
            ("SER-014", "Nội soi vệ sinh giàn lạnh điều hòa", "Điện lạnh", 550000.0, 1.5),
            ("SER-015", "Hút chân không & nạp gas điều hòa R134a", "Điện lạnh", 400000.0, 1.0),
            ("SER-016", "Thay nước làm mát động cơ tuần hoàn", "Động cơ", 200000.0, 0.8),
            ("SER-017", "Thay dầu hộp số tự động tuần hoàn", "Hộp số", 500000.0, 1.5),
            ("SER-018", "Vệ sinh khoang máy bằng hơi nước nóng", "Chăm sóc", 600000.0, 2.0),
            ("SER-019", "Kiểm tra chẩn đoán hệ thống điện OBD-II", "Điện tử", 200000.0, 0.5),
            ("SER-020", "Đánh bóng sơn toàn thân xe 3 bước", "Chăm sóc", 1500000.0, 5.0)
        ]
        services = []
        for code, name, cat, labor, hours in service_catalog:
            s = Service(code=code, name=name, category=cat, labor_cost=labor, estimated_hours=hours)
            services.append(s)
        db.add_all(services)
        db.flush()

        # 6. 50+ SPARE PARTS
        parts_catalog = [
            ("PAR-001", "Dầu nhớt Castrol Magnatec 5W-30 (Can 4L)", "Castrol", 650000.0, 480000.0, 45, 10),
            ("PAR-002", "Dầu nhớt Mobil 1 Gold 0W-40 (Bình 1L)", "Mobil", 280000.0, 210000.0, 60, 15),
            ("PAR-003", "Dầu nhớt Motul H-Tech 100 Plus 5W-30 (Can 4L)", "Motul", 720000.0, 540000.0, 30, 8),
            ("PAR-004", "Lọc dầu động cơ Toyota Camry/Vios", "Denso", 150000.0, 95000.0, 80, 20),
            ("PAR-005", "Lọc dầu động cơ Honda Civic/CR-V", "Honda OEM", 160000.0, 105000.0, 75, 20),
            ("PAR-006", "Lọc dầu động cơ Mazda 3/CX-5", "Mazda OEM", 155000.0, 100000.0, 70, 15),
            ("PAR-007", "Lọc dầu động cơ Hyundai/Kia", "Mobis", 140000.0, 85000.0, 85, 20),
            ("PAR-008", "Lọc gió động cơ Toyota Camry", "Denso", 280000.0, 180000.0, 40, 10),
            ("PAR-009", "Lọc gió động cơ Honda CR-V", "Honda OEM", 290000.0, 190000.0, 35, 10),
            ("PAR-010", "Lọc gió động cơ Mazda CX-5", "Mazda OEM", 300000.0, 195000.0, 30, 8),
            ("PAR-011", "Lọc gió điều hòa than hoạt tính Toyota", "Denso", 350000.0, 220000.0, 50, 12),
            ("PAR-012", "Lọc gió điều hòa than hoạt tính Honda", "Bosch", 360000.0, 230000.0, 45, 10),
            ("PAR-013", "Má phanh trước Toyota Camry", "Brembo", 1250000.0, 850000.0, 25, 5),
            ("PAR-014", "Má phanh sau Toyota Camry", "Brembo", 950000.0, 650000.0, 20, 5),
            ("PAR-015", "Má phanh trước Honda CR-V", "Nissin", 1150000.0, 780000.0, 25, 5),
            ("PAR-016", "Má phanh sau Honda CR-V", "Nissin", 890000.0, 600000.0, 22, 5),
            ("PAR-017", "Má phanh trước Mazda CX-5", "Akebono", 1200000.0, 820000.0, 20, 5),
            ("PAR-018", "Bugi Iridium Denso SK20R11", "Denso", 220000.0, 145000.0, 120, 30),
            ("PAR-019", "Bugi Iridium NGK Laser ILZKR7B11", "NGK", 240000.0, 160000.0, 100, 25),
            ("PAR-020", "Ắc quy GS MF 55D23L (12V - 60Ah)", "GS", 1650000.0, 1250000.0, 18, 4),
            ("PAR-021", "Ắc quy Varta Q85 EFB (12V - 65Ah cho i-Stop)", "Varta", 2450000.0, 1900000.0, 15, 3),
            ("PAR-022", "Ắc quy Amaron Din 65 (12V - 65Ah)", "Amaron", 2100000.0, 1600000.0, 14, 3),
            ("PAR-023", "Nước làm mát động cơ pha sẵn Coolant (Can 4L)", "Toyota", 380000.0, 260000.0, 35, 8),
            ("PAR-024", "Dầu hộp số tự động ATF WS (Can 4L)", "Toyota", 850000.0, 620000.0, 25, 6),
            ("PAR-025", "Dầu phanh cao cấp DOT 4 (Chai 1L)", "Bosch", 180000.0, 115000.0, 50, 10),
            ("PAR-026", "Dung dịch vệ sinh kim phun xăng Techron", "Caltex", 160000.0, 110000.0, 65, 15),
            ("PAR-027", "Dung dịch súc rửa động cơ Engine Flush", "Liqui Moly", 220000.0, 150000.0, 40, 10),
            ("PAR-028", "Gạt mưa silicon đa năng Bosch AeroTwin 24 inch", "Bosch", 280000.0, 180000.0, 30, 6),
            ("PAR-029", "Gạt mưa silicon đa năng Bosch AeroTwin 18 inch", "Bosch", 240000.0, 150000.0, 30, 6),
            ("PAR-030", "Dây curoa tổng Gates 6PK2120", "Gates", 450000.0, 310000.0, 20, 4),
            ("PAR-031", "Cao su chân máy trước Toyota Vios", "Toyota OEM", 680000.0, 480000.0, 12, 3),
            ("PAR-032", "Rô-tuyn cân bằng trước Mazda 3", "555 Japan", 380000.0, 250000.0, 16, 4),
            ("PAR-033", "Rô-tuyn lái trong Honda Civic", "555 Japan", 420000.0, 280000.0, 14, 4),
            ("PAR-034", "Càng chữ A trước phải Hyundai SantaFe", "Mobis", 1850000.0, 1350000.0, 8, 2),
            ("PAR-035", "Giảm xóc trước trái Toyota Fortuner", "KYB", 1950000.0, 1400000.0, 10, 2),
            ("PAR-036", "Giảm xóc trước phải Toyota Fortuner", "KYB", 1950000.0, 1400000.0, 10, 2),
            ("PAR-037", "Lốp xe Michelin Primacy 4 215/55R17", "Michelin", 2850000.0, 2350000.0, 16, 4),
            ("PAR-038", "Lốp xe Bridgestone Turanza ER300 205/55R16", "Bridgestone", 2150000.0, 1750000.0, 20, 4),
            ("PAR-039", "Bơm xăng nguyên cụm Toyota Vios", "Denso", 2200000.0, 1650000.0, 6, 2),
            ("PAR-040", "Két nước làm mát nhôm Honda City", "Denso", 1850000.0, 1350000.0, 7, 2),
            ("PAR-041", "Van hằng nhiệt động cơ Toyota", "Tama Japan", 350000.0, 240000.0, 18, 4),
            ("PAR-042", "Cảm biến oxy trước xúc tác Mazda 3", "Denso", 1450000.0, 1050000.0, 8, 2),
            ("PAR-043", "Cảm biến lưu lượng khí nạp MAF Toyota", "Denso", 1650000.0, 1200000.0, 6, 2),
            ("PAR-044", "Bình xịt khử mùi dàn lạnh điều hòa", "Wurth", 190000.0, 130000.0, 50, 10),
            ("PAR-045", "Bóng đèn pha Xenon HID D2S 35W", "Philips", 650000.0, 450000.0, 24, 6),
            ("PAR-046", "Bóng đèn LED Philips Ultinon H7", "Philips", 1200000.0, 850000.0, 15, 4),
            ("PAR-047", "Còi sên âm thanh trầm bổng 12V", "Denso", 350000.0, 230000.0, 30, 8),
            ("PAR-048", "Chất chống bám nước kính lái Aquapel", "PPG", 250000.0, 160000.0, 40, 10),
            ("PAR-049", "Mỡ bôi trơn chốt caliper phanh chịu nhiệt", "Permatex", 120000.0, 75000.0, 45, 10),
            ("PAR-050", "Chai phủ gầm gốc nước chống rỉ sét", "3M", 350000.0, 240000.0, 40, 8)
        ]
        parts = []
        for code, name, brand, sell_price, cost_price, stock, min_stock in parts_catalog:
            p = Part(
                code=code, name=name, brand=brand, unit_price=sell_price,
                cost_price=cost_price, stock_quantity=stock, min_stock_alert=min_stock
            )
            parts.append(p)
        db.add_all(parts)
        db.flush()

        # 7. 30+ REPAIR ORDERS & INVOICES & PAYMENTS
        now = datetime.utcnow()
        ro_statuses = [
            RepairOrderStatus.COMPLETED, RepairOrderStatus.COMPLETED, RepairOrderStatus.COMPLETED,
            RepairOrderStatus.IN_REPAIR, RepairOrderStatus.WAITING_CUSTOMER_APPROVAL,
            RepairOrderStatus.INSPECTING, RepairOrderStatus.RECEIVED, RepairOrderStatus.COMPLETED
        ]

        repair_orders = []
        invoices = []
        payments = []

        for i in range(1, 31):
            v = vehicles[(i - 1) % len(vehicles)]
            c = v.owner
            st = ro_statuses[(i - 1) % len(ro_statuses)]
            assigned_tech = tech1 if i % 2 == 1 else tech2

            # 1. Create VehicleReception
            rec = VehicleReception(
                reception_code=f"REC-2026-{i:06d}",
                customer_id=c.id,
                vehicle_id=v.id,
                mileage=v.current_mileage - ((30 - i) * 200),
                fuel_level="3/4" if i % 2 == 0 else "1/2",
                customer_complaint=f"Kiểm tra bảo dưỡng định kỳ & chẩn đoán rung lắc xe #{i}",
                received_by_id=receptionist.id,
                received_at=now - timedelta(days=(30 - i))
            )
            db.add(rec)
            db.flush()

            # 2. Create RepairOrder
            ro = RepairOrder(
                code=f"RO-2026-{i:06d}",
                customer_id=c.id,
                vehicle_id=v.id,
                reception_id=rec.id,
                technician_id=assigned_tech.id,
                receptionist_id=receptionist.id,
                mileage_in=rec.mileage,
                customer_complaint=rec.customer_complaint,
                technical_diagnosis=f"Phát hiện dầu máy cũ quá hạn, má phanh mòn 60% trên xe {v.brand} {v.model}",
                status=st,
                created_at=now - timedelta(days=(30 - i)),
                completed_at=(now - timedelta(days=(30 - i) - 1)) if st == RepairOrderStatus.COMPLETED else None
            )
            db.add(ro)
            db.flush()

            # Add inspection item
            insp = Inspection(
                repair_order_id=ro.id,
                category=InspectionCategory.BRAKES,
                item="Má phanh trước",
                condition="Độ dày còn 3.5mm, có hiện tượng chai bề mặt",
                severity=InspectionSeverity.WARNING,
                technician_note="Khuyến nghị thay má phanh và láng đĩa để phanh ăn",
                created_at=ro.created_at
            )
            db.add(insp)

            # Add services and parts
            s1 = services[i % len(services)]
            p1 = parts[i % len(parts)]
            p2 = parts[(i + 3) % len(parts)]

            # RepairOrderService
            ros = RepairOrderService(
                repair_order_id=ro.id,
                service_id=s1.id,
                quantity=1.0,
                unit_price=s1.labor_cost,
                subtotal=s1.labor_cost
            )
            db.add(ros)

            # RepairOrderParts
            rop1 = RepairOrderPart(
                repair_order_id=ro.id,
                part_id=p1.id,
                quantity=1,
                unit_price=p1.unit_price,
                subtotal=p1.unit_price
            )
            rop2 = RepairOrderPart(
                repair_order_id=ro.id,
                part_id=p2.id,
                quantity=2,
                unit_price=p2.unit_price,
                subtotal=p2.unit_price * 2
            )
            db.add_all([rop1, rop2])

            subtotal = s1.labor_cost + p1.unit_price + (p2.unit_price * 2)
            vat = round(subtotal * 0.10, 2)
            total = subtotal + vat

            ro.estimated_cost = total
            ro.final_cost = total

            # Create Quotation
            qo = Quotation(
                quotation_code=f"QO-2026-{i:06d}",
                repair_order_id=ro.id,
                customer_id=c.id,
                vehicle_id=v.id,
                quotation_date=ro.created_at,
                valid_until=ro.created_at + timedelta(days=15),
                subtotal=subtotal,
                vat_rate=0.10,
                vat=vat,
                total=total,
                status=QuotationStatus.APPROVED if st in [RepairOrderStatus.IN_REPAIR, RepairOrderStatus.COMPLETED] else QuotationStatus.PENDING_APPROVAL,
                approval_status="APPROVED" if st in [RepairOrderStatus.IN_REPAIR, RepairOrderStatus.COMPLETED] else "PENDING"
            )
            db.add(qo)

            # If completed, create Invoice and Payment
            if st == RepairOrderStatus.COMPLETED:
                inv = Invoice(
                    invoice_number=f"INV-2026-{i:06d}",
                    repair_order_id=ro.id,
                    customer_id=c.id,
                    vehicle_id=v.id,
                    invoice_date=ro.completed_at or now,
                    subtotal=subtotal,
                    vat=vat,
                    tax_amount=vat,
                    total=total,
                    total_amount=total,
                    paid_amount=total,
                    balance_due=0.0,
                    remaining_amount=0.0,
                    status=InvoiceStatus.PAID
                )
                db.add(inv)
                db.flush()

                pay = Payment(
                    payment_code=f"PAY-2026-{i:06d}",
                    invoice_id=inv.id,
                    amount=total,
                    payment_method=PaymentMethod.BANK_TRANSFER if i % 2 == 0 else PaymentMethod.CASH,
                    transaction_reference=f"VTVPAY-{i:06d}",
                    payment_date=inv.invoice_date,
                    cashier_id=cashier.id
                )
                db.add(pay)

        db.commit()
        print("✅ Nạp thành công toàn bộ dữ liệu mẫu:")
        print("   - 5 Users với 4 Vai trò (Admin, Lễ tân, 2 Kỹ thuật viên, Thu ngân)")
        print("   - 22 Khách hàng & 32 Phương tiện")
        print("   - 20 Dịch vụ kỹ thuật & 50 Phụ tùng kho")
        print("   - 30 Phiếu sửa chữa & Tiếp nhận xe chi tiết")
        print("   - 30 Báo giá & 15+ Hóa đơn, Giao dịch thanh toán thực tế")

    except Exception as e:
        print(f"❌ Lỗi khi nạp dữ liệu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
