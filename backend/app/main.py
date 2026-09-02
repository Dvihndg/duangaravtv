import os
import sys

# Ensure root directory is in sys.path for relative imports on Vercel
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import engine, Base, get_db, SessionLocal
from backend.app.routers import (
    auth, customers, appointments, inventory, repair_orders, invoices, ai, analytics, customer_requests,
    receptions, quotations, audit_logs, settings as settings_router
)

# Create database tables automatically with fault safety
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[DB Warning] Unable to auto-create tables on startup: {e}")

def ensure_db_columns():
    try:
        inspector = inspect(engine)
        if "ai_logs" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("ai_logs")]
            with engine.connect() as conn:
                new_cols = [
                    ("latency_ms", "FLOAT DEFAULT 0.0"),
                    ("token_prompt_count", "INTEGER DEFAULT 0"),
                    ("token_completion_count", "INTEGER DEFAULT 0"),
                    ("token_total_count", "INTEGER DEFAULT 0"),
                    ("estimated_cost_usd", "FLOAT DEFAULT 0.0"),
                    ("status", "VARCHAR(30) DEFAULT 'success'"),
                    ("top1_accuracy", "FLOAT DEFAULT 1.0"),
                    ("parts_accuracy", "FLOAT DEFAULT 1.0"),
                    ("price_variance", "FLOAT DEFAULT 0.0"),
                ]
                for name, d_type in new_cols:
                    if name not in columns:
                        conn.execute(text(f"ALTER TABLE ai_logs ADD COLUMN {name} {d_type}"))
                conn.commit()
    except Exception as e:
        print(f"Migration notice: {e}")

try:
    ensure_db_columns()
except Exception as e:
    print(f"[DB Columns Warning] {e}")

def ensure_default_seed_users():
    try:
        from backend.app.models import User, UserRole, Service, Part
        from backend.app.auth import get_password_hash
        db = SessionLocal()
        try:
            if not db.query(User).filter(User.username == "admin").first():
                admin_user = User(
                    username="admin",
                    email="admin@garage.com",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Nguyên Van Quan Ly",
                    role=UserRole.MANAGER,
                    phone="0901111111"
                )
                letan_user = User(
                    username="letan",
                    email="letan@garage.com",
                    hashed_password=get_password_hash("letan123"),
                    full_name="Tran Thi Le Tan",
                    role=UserRole.RECEPTIONIST,
                    phone="0902222222"
                )
                tech_user = User(
                    username="kythuat",
                    email="kythuat@garage.com",
                    hashed_password=get_password_hash("tech123"),
                    full_name="Le Hoang Ky Thuat",
                    role=UserRole.TECHNICIAN,
                    phone="0903333333"
                )
                cashier_user = User(
                    username="thungan",
                    email="thungan@garage.com",
                    hashed_password=get_password_hash("cashier123"),
                    full_name="Pham Thi Thu Ngan",
                    role=UserRole.CASHIER,
                    phone="0904444444"
                )
                db.add_all([admin_user, letan_user, tech_user, cashier_user])
                db.commit()

            if not db.query(Service).first():
                s1 = Service(code="DV-001", name="Bảo dưỡng định kỳ 5,000 km", category="Bảo dưỡng", price=450000, estimated_minutes=60)
                s2 = Service(code="DV-002", name="Chẩn đoán lỗi động cơ (Scan OBD-II)", category="Chẩn đoán", price=300000, estimated_minutes=45)
                s3 = Service(code="DV-003", name="Thay dầu nhớt & Lọc nhớt động cơ", category="Bảo dưỡng", price=150000, estimated_minutes=30)
                db.add_all([s1, s2, s3])
                db.commit()

            if not db.query(Part).first():
                p1 = Part(code="PT-001", name="Dầu nhớt Fully Synthetic 5W-30 (Can 4L)", category="Hóa chất / Dầu nhớt", unit="Can", cost_price=650000, selling_price=850000, stock_quantity=45, min_stock=10)
                p2 = Part(code="PT-002", name="Lọc nhớt động cơ Toyota Camry/Corolla", category="Phụ tùng thay thế", unit="Cái", cost_price=120000, selling_price=180000, stock_quantity=30, min_stock=5)
                p3 = Part(code="PT-003", name="Má phanh trước Honda CR-V (Bộ 4 miếng)", category="Phụ tùng thay thế", unit="Bộ", cost_price=850000, selling_price=1250000, stock_quantity=15, min_stock=4)
                db.add_all([p1, p2, p3])
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"[DB Auto Seed Notice] {e}")

try:
    ensure_default_seed_users()
except Exception as e:
    print(f"[Auto Seed Exception] {e}")

from starlette.types import ASGIApp, Scope, Receive, Send
from urllib.parse import urlparse

class VercelPathRewriteMiddleware:
    """
    Middleware to resolve original Vercel serverless request paths when Vercel rewrites 
    requests to /api/index.py. Restores scope['path'] from x-matched-path or x-real-url.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            raw_path = scope.get("path", "")
            
            # If path was rewritten by Vercel to /api/index.py or /api/index
            if raw_path in ("/api/index.py", "/api/index", "/api", "/api/"):
                x_matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
                x_real_url = headers.get(b"x-real-url", b"").decode("utf-8")
                
                if x_matched_path and not x_matched_path.startswith("/api/index"):
                    scope["path"] = x_matched_path
                elif x_real_url:
                    parsed = urlparse(x_real_url)
                    if parsed.path:
                        scope["path"] = parsed.path
                        
        await self.app(scope, receive, send)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Hệ thống Quản lý Garage Ô tô Tích hợp AI (FastAPI + Modern SPA + Gemini AI)"
)

# Vercel Path Fixer Middleware
app.add_middleware(VercelPathRewriteMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
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

# Serve Frontend from Project Root
@app.get("/")
def read_root():
    index_path = os.path.join(root_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Garage VTV API Server Operating"}

@app.get("/admin")
@app.get("/admin.html")
def read_admin():
    admin_path = os.path.join(root_dir, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"detail": "Admin HTML not found"}

@app.get("/customer")
@app.get("/customer.html")
def read_customer():
    cust_path = os.path.join(root_dir, "customer.html")
    if not os.path.exists(cust_path):
        cust_path = os.path.join(root_dir, "index.html")
    if os.path.exists(cust_path):
        return FileResponse(cust_path)
    return {"detail": "Customer HTML not found"}

@app.get("/login")
@app.get("/login.html")
def read_login():
    login_path = os.path.join(root_dir, "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"detail": "Login HTML not found"}

@app.get("/logo.png")
@app.get("/favicon.ico")
def read_logo():
    logo_path = os.path.join(root_dir, "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    return {"detail": "Logo not found"}

@app.get("/styles.css")
def read_styles():
    css_path = os.path.join(root_dir, "styles.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return {"detail": "Styles not found"}

@app.get("/app.js")
def read_app_js():
    js_path = os.path.join(root_dir, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return {"detail": "App JS not found"}

@app.get("/health")
def health_check():
    db_status = "connected"
    db_type = "unknown"
    table_count = 0
    error_msg = None
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_type = engine.name
            inspector = inspect(engine)
            table_count = len(inspector.get_table_names())
        finally:
            db.close()
    except Exception as e:
        db_status = "degraded"
        error_msg = str(e)

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "project": settings.PROJECT_NAME,
        "database": {
            "status": db_status,
            "engine": db_type,
            "table_count": table_count,
            "error": error_msg
        }
    }
