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
os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routers import (
    auth, customers, appointments, inventory, repair_orders, invoices, ai, analytics,
    customer_requests, receptions, quotations, audit_logs, settings as settings_router
)
from backend.app.main import health_check, read_api_root, debug_endpoint

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Hệ thống Quản lý Garage Ô tô Tích hợp AI (FastAPI + Modern SPA + Gemini AI)"
)

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

# Direct endpoints
app.add_api_route("/health", health_check, methods=["GET"])
app.add_api_route("/api/health", health_check, methods=["GET"])
app.add_api_route("/api/v1/health", health_check, methods=["GET"])
app.add_api_route("/api", read_api_root, methods=["GET"])
app.add_api_route("/api/", read_api_root, methods=["GET"])
app.add_api_route("/", read_api_root, methods=["GET"])
app.add_api_route("/api/debug", debug_endpoint, methods=["GET", "POST"])
app.add_api_route("/api/v1/debug", debug_endpoint, methods=["GET", "POST"])
