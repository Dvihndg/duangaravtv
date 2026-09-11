import sys
import os
import shutil
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Top-level FastAPI instance created first so Vercel can always load the module
app = FastAPI(title="Garage VTV API")

import_error = None

try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    tmp_db = "/tmp/garage.db"
    if not os.path.exists(tmp_db):
        root_db = os.path.join(BASE_DIR, "garage.db")
        if os.path.exists(root_db):
            try:
                shutil.copy2(root_db, tmp_db)
            except Exception:
                pass
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

    from backend.app.config import settings
    from backend.app.database import engine, SessionLocal
    from backend.app.routers import (
        auth, customers, appointments, inventory, repair_orders, invoices, ai, analytics,
        customer_requests, receptions, quotations, audit_logs, settings as settings_router
    )

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

except Exception as e:
    import_error = traceback.format_exc()
    print(f"[Import Diagnostic]: {import_error}")

@app.get("/api/v1/health")
@app.get("/health")
@app.get("/api")
def health_check():
    if import_error:
        return JSONResponse(
            status_code=500,
            content={
                "status": "import_failed",
                "error": import_error.splitlines()[-1] if import_error else "Unknown",
                "traceback": import_error.splitlines() if import_error else []
            }
        )
    return {
        "status": "ok",
        "message": "All routers and database loaded successfully on Vercel!"
    }
