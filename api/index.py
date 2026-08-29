import os
import sys

# Root path resolution for Vercel Serverless environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Fix Vercel Read-Only Filesystem for SQLite fallback
db_url = os.getenv("DATABASE_URL", "")
if not db_url or "sqlite" in db_url:
    try:
        import shutil
        tmp_db = "/tmp/garage.db"
        root_db = os.path.join(BASE_DIR, "garage.db")
        if not os.path.exists(tmp_db) and os.path.exists(root_db):
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
    @app.get("/health")
    def health_fallback():
        return {"status": "degraded", "fallback_active": True, "error": str(e)}
    @app.get("/api/v1/{path:path}")
    def api_fallback(path: str):
        return {"status": "degraded", "fallback_active": True, "path": path}

handler = app
__all__ = ["app", "handler"]
