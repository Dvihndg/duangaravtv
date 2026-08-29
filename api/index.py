import os
import sys

# Root path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Fix Vercel Read-Only Filesystem for SQLite
if os.getenv("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
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
except Exception as err:
    print(f"[Vercel Startup Warning] Falling back to lightweight serverless app: {err}")
    from fastapi import FastAPI
    app = FastAPI(title="Garage VTV Fallback API")

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "mode": "serverless_fallback"}

    @app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def api_fallback(path: str):
        return {"status": "ok", "message": f"Serverless fallback active for /api/v1/{path}"}
