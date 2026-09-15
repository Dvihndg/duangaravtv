import os
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# SQLite fallback in /tmp for Vercel Serverless environment
tmp_db = "/tmp/garage.db"
if not os.path.exists(tmp_db):
    root_db = os.path.join(BASE_DIR, "garage.db")
    if os.path.exists(root_db):
        try:
            shutil.copy2(root_db, tmp_db)
        except Exception:
            pass

vtv_db = os.environ.get("VTV_GARAGE_DB")
pg_url = os.environ.get("POSTGRES_URL")
sb_url = os.environ.get("SUPABASE_URL")

if vtv_db:
    os.environ["DATABASE_URL"] = vtv_db
elif pg_url:
    os.environ["DATABASE_URL"] = pg_url
elif sb_url:
    os.environ["DATABASE_URL"] = sb_url
elif not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

app = FastAPI(
    title="Hệ thống Quản lý Garage Ô tô Tích hợp AI",
    version="1.0.0",
    description="Hệ thống Quản lý Garage Ô tô Tích hợp AI"
)

from backend.app.config import settings
from backend.app.database import engine, SessionLocal
from backend.app.routers import (
    auth, customers, appointments, inventory, repair_orders, invoices, ai, analytics,
    customer_requests, receptions, quotations, audit_logs, settings as settings_router
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API Routers
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(appointments.router)
app.include_router(inventory.router)
app.include_router(repair_orders.router)
app.include_router(invoices.router)
app.include_router(ai.router)
app.include_router(analytics.router)
app.include_router(customer_requests.router, prefix="/api/v1")
app.include_router(receptions.router, prefix="/api/v1")
app.include_router(quotations.router, prefix="/api/v1")
app.include_router(audit_logs.router)
app.include_router(settings_router.router)

@app.get("/api/v1/health")
@app.get("/api/health")
@app.get("/health")
def health_check():
    db_status = "connected"
    table_count = 0
    error_msg = None
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            inspector = inspect(engine)
            table_count = len(inspector.get_table_names())
        finally:
            db.close()
    except Exception as e:
        db_status = "degraded"
        error_msg = str(e)

    return {
        "status": "ok" if "connected" in db_status else "degraded",
        "project": settings.PROJECT_NAME,
        "database": {
            "status": db_status,
            "engine": engine.name,
            "table_count": table_count,
            "error": error_msg
        }
    }

@app.get("/api")
@app.get("/api/")
@app.get("/")
def read_api_root():
    return {
        "status": "ok",
        "message": "Garage VTV Backend API is running on Vercel",
        "endpoints": {
            "health": "/api/v1/health",
            "docs": "/docs",
            "setup": "/api/v1/setup-db",
            "ai_open": "/api/v1/ai/assistant/open"
        }
    }

@app.get("/api/v1/setup-db")
def auto_setup_db():
    from backend.app.models import Base, User, UserRole
    from backend.app.auth import get_password_hash
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Check if admin exists
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                new_admin = User(
                    username="admin",
                    email="admin@vtvgarage.com",
                    hashed_password=get_password_hash("password"),
                    full_name="Quản trị viên",
                    role=UserRole.MANAGER,
                    phone="0987654321",
                    is_active=True
                )
                db.add(new_admin)
                db.commit()
                return {"status": "success", "message": "Đã tạo bảng và tài khoản admin thành công!"}
            return {"status": "success", "message": "Database đã được setup từ trước, đã có tài khoản admin."}
        finally:
            db.close()
    except Exception as e:
        return {"status": "error", "error": str(e)}
