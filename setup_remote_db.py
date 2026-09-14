import sys
import os

if len(sys.argv) < 2:
    print("Vui lòng cung cấp chuỗi kết nối DATABASE_URL.")
    print("Ví dụ: python setup_remote_db.py postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres")
    sys.exit(1)

db_url = sys.argv[1]
# Sửa protocol cho tương thích với SQLAlchemy nếu cần
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

print("Connecting to DB...")

# Cấu hình biến môi trường trước khi import các module của app
os.environ["DATABASE_URL"] = db_url

# Import các thành phần của Backend
try:
    from backend.app.database import engine, Base
    from backend.app.main import init_db_background
    import backend.app.models  # Đảm bảo các models được load
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

print("Initializing tables and seed data...")
try:
    # Bỏ qua kiểm tra VERCEL để ép chạy hàm init
    if "VERCEL" in os.environ:
        del os.environ["VERCEL"]
        
    init_db_background()
    print("SUCCESS: Tables and seed data created!")
except Exception as e:
    print(f"ERROR initializing DB: {e}")
