import os
import sys
import shutil
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Top-level FastAPI instance for Vercel AST scanner
app = FastAPI(title="Garage VTV API", version="1.0.0")

init_error = None

try:
    # 1. SQLite fallback setup for Vercel serverless
    tmp_db = "/tmp/garage.db"
    if not os.path.exists(tmp_db):
        root_db = os.path.join(BASE_DIR, "garage.db")
        if os.path.exists(root_db):
            try:
                shutil.copy2(root_db, tmp_db)
            except Exception as copy_e:
                print(f"Copy error: {copy_e}")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

    # 2. Import middleware, routers and handlers
    from fastapi.middleware.cors import CORSMiddleware
    from backend.app.config import settings
    from backend.app.main import VercelPathRewriteMiddleware, global_exception_handler, health_check, read_api_root, debug_endpoint
    from backend.app.routers import (
        auth, customers, appointments, inventory, repair_orders, invoices, ai, analytics,
        customer_requests, receptions, quotations, audit_logs, settings as settings_router
    )

    app.add_middleware(VercelPathRewriteMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(Exception, global_exception_handler)

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

    app.add_api_route("/health", health_check, methods=["GET"])
    app.add_api_route("/api/health", health_check, methods=["GET"])
    app.add_api_route("/api/v1/health", health_check, methods=["GET"])
    app.add_api_route("/api", read_api_root, methods=["GET"])
    app.add_api_route("/api/", read_api_root, methods=["GET"])
    app.add_api_route("/api/debug", debug_endpoint, methods=["GET", "POST"])
    app.add_api_route("/api/v1/debug", debug_endpoint, methods=["GET", "POST"])

except Exception as e:
    init_error = traceback.format_exc()
    print(f"[FATAL Vercel Init Error]: {init_error}")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    def fatal_error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "FastAPI Startup Failure on Vercel",
                "detail": str(e),
                "traceback": init_error.split("\n"),
                "base_dir": BASE_DIR,
                "sys_path": sys.path[:5]
            }
        )
