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

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Hệ thống Quản lý Garage Ô tô Tích hợp AI (FastAPI + Modern SPA + Gemini AI)"
)

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
@app.get("/api/index.py")
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
