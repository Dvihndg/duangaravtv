import os
import sys
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
                import shutil
                shutil.copy2(root_db, tmp_db)
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"
    except Exception as e:
        print(f"[Vercel Startup Notice] SQLite /tmp setup: {e}")

try:
    from backend.app.main import app
except Exception as e:
    import traceback
    print(f"[Vercel Serverless Startup Exception]: {e}")
    traceback.print_exc()
    from fastapi import FastAPI
    app = FastAPI(title="Garage VTV Fallback App")
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    def api_fallback(path: str):
        return {"status": "degraded", "fallback_active": True, "path": path, "error": str(e)}

async def handler(scope, receive, send):
    if scope.get("type") in ("http", "websocket"):
        headers = dict(scope.get("headers", []))
        raw_path = scope.get("path", "")
        
        if raw_path in ("/api/index.py", "/api/index", "/api", "/api/", "/index.py", ""):
            for h in (b"x-forwarded-uri", b"x-invoke-path", b"x-matched-path", b"x-real-url"):
                val = headers.get(h, b"").decode("utf-8", errors="ignore")
                if val and not val.startswith("/api/index") and not val.startswith("/index.py"):
                    if "://" in val:
                        parsed = urlparse(val)
                        if parsed.path:
                            scope["path"] = parsed.path
                            break
                    else:
                        scope["path"] = val.split("?")[0]
                        break

    await app(scope, receive, send)

__all__ = ["app", "handler"]
