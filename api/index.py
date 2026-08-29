import os
import sys
import shutil

# Root path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Fix Vercel Read-Only Filesystem for SQLite
if os.getenv("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    tmp_db = "/tmp/garage.db"
    root_db = os.path.join(BASE_DIR, "garage.db")
    if not os.path.exists(tmp_db):
        if os.path.exists(root_db):
            try:
                shutil.copy2(root_db, tmp_db)
            except Exception as e:
                print(f"[Vercel Startup] Could not copy garage.db to /tmp: {e}")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

from backend.app.main import app
