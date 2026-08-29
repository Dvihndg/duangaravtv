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

from backend.app.main import app

# Export both app and handler for Vercel WSGI/ASGI Serverless runtime
handler = app
__all__ = ["app", "handler"]
