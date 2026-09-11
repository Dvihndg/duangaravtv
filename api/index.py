import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from sqlalchemy import text, inspect
from backend.app.database import engine, SessionLocal

app = FastAPI()

@app.get("/api/v1/health")
@app.get("/health")
@app.get("/api")
def health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        tables = len(inspect(engine).get_table_names())
        return {"status": "ok", "engine": engine.name, "tables": tables}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()
