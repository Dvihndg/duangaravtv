import os
import sys
import shutil

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# SQLite fallback in /tmp for Vercel Serverless environment
db_url = os.getenv("DATABASE_URL", "")
if not db_url or "sqlite" in db_url:
    try:
        tmp_db = "/tmp/garage.db"
        if not os.path.exists(tmp_db):
            root_db = os.path.join(BASE_DIR, "garage.db")
            if os.path.exists(root_db):
                shutil.copy2(root_db, tmp_db)
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"
    except Exception as e:
        print(f"[Vercel Startup Notice] SQLite /tmp setup: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.main import VercelPathRewriteMiddleware, global_exception_handler
from backend.app.routers import (
    auth, customers, appointments, inventory, repair_orders, invoices, ai, analytics,
    customer_requests, receptions, quotations, audit_logs, settings as settings_router
)
from backend.app.main import health_check, read_api_root, debug_endpoint

# Explicit top-level FastAPI instance required by Vercel AST scanner
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Hệ thống Quản lý Garage Ô tô Tích hợp AI (FastAPI + Modern SPA + Gemini AI)"
)

# Vercel Path Fixer Middleware
app.add_middleware(VercelPathRewriteMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)

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
app.add_api_route("/api/debug", debug_endpoint, methods=["GET", "POST"])
app.add_api_route("/api/v1/debug", debug_endpoint, methods=["GET", "POST"])
