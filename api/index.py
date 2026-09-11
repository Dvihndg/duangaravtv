import os
import sys
import shutil
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send
from urllib.parse import urlparse

# Root path resolution for Vercel Serverless environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Fix Vercel Read-Only Filesystem for SQLite fallback
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

# Vercel Path Fixer Middleware
class VercelPathRewriteMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            raw_path = scope.get("path", "")
            
            # 1. Query parameter override (__vpath__)
            query_str = scope.get("query_string", b"").decode("utf-8", errors="ignore")
            if "__vpath__=" in query_str:
                from urllib.parse import parse_qs, urlencode
                qs = parse_qs(query_str)
                if "__vpath__" in qs:
                    scope["path"] = qs.pop("__vpath__")[0]
                    scope["query_string"] = urlencode(qs, doseq=True).encode("utf-8")
                    raw_path = scope["path"]

            # 2. If path was rewritten by Vercel to /api or /api/index
            if raw_path in ("/api/index.py", "/api/index", "/api", "/api/", "/index.py", ""):
                for header_key in (
                    b"x-vercel-matched-path",
                    b"x-forwarded-uri",
                    b"x-invoke-path",
                    b"x-matched-path",
                    b"x-real-url",
                    b"x-original-uri"
                ):
                    val = headers.get(header_key, b"").decode("utf-8", errors="ignore")
                    if val and not val.startswith("/api/index") and not val.startswith("/index.py"):
                        if "://" in val:
                            parsed = urlparse(val)
                            if parsed.path:
                                scope["path"] = parsed.path
                                break
                        else:
                            scope["path"] = val.split("?")[0]
                            break
                        
        await self.app(scope, receive, send)

# Top-level explicit FastAPI instance required by Vercel's detector
app = FastAPI(
    title="Hệ thống Quản lý Garage Tích hợp AI",
    version="1.0.0",
    description="Backend API Garage VTV running on Vercel Serverless"
)

app.add_middleware(VercelPathRewriteMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Include all application routers
try:
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
    import traceback
    print(f"[Vercel Router Mount Error]: {e}")
    traceback.print_exc()

# Endpoints
@app.get("/api")
@app.get("/api/")
@app.get("/api/index.py")
def read_api_root():
    return {
        "status": "ok",
        "message": "Garage VTV Backend API is running on Vercel",
        "endpoints": {
            "health": "/api/v1/health",
            "docs": "/docs",
            "ai_open": "/api/v1/ai/assistant/open"
        }
    }

@app.get("/health")
@app.get("/api/health")
@app.get("/api/v1/health")
def health_check():
    db_status = "connected"
    db_type = "unknown"
    table_count = 0
    error_msg = None
    try:
        from backend.app.database import SessionLocal, engine
        from sqlalchemy import text, inspect
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
        "project": "Hệ thống Quản lý Garage Tích hợp AI",
        "database": {
            "status": db_status,
            "engine": db_type,
            "table_count": table_count,
            "error": error_msg
        }
    }
