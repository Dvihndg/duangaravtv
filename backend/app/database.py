import os
import shutil
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ─── SQLite /tmp Setup for Vercel Serverless ─────────────────────────────────
tmp_db_path = "/tmp/garage.db"
if not os.path.exists(tmp_db_path):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for candidate in [
        os.path.join(root_dir, "garage.db"),
        os.path.join(os.getcwd(), "garage.db"),
        "garage.db"
    ]:
        if os.path.exists(candidate):
            try:
                shutil.copy2(candidate, tmp_db_path)
                break
            except Exception:
                pass

# ─── Database URL Resolution ──────────────────────────────────────────────────
db_url = os.getenv("DATABASE_URL", "")
is_vercel = bool(os.getenv("VERCEL"))

# On Vercel, Supabase direct connection (:5432) times out because AWS Lambda lacks IPv6.
# Use bundled /tmp/garage.db containing all live server data unless an IPv4 pooler is configured.
if is_vercel and (":5432" in db_url or "supabase.co:5432" in db_url or not db_url):
    db_url = f"sqlite:///{tmp_db_path}"
elif not db_url:
    db_url = f"sqlite:///{tmp_db_path}" if os.path.exists(tmp_db_path) else "sqlite:///./garage.db"

# Fix: Supabase/Heroku uses "postgres://" or "postgresql://"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Dynamically use pg8000 (Pure Python) if installed, otherwise fallback to standard psycopg2
if db_url.startswith("postgresql://"):
    try:
        import pg8000
        db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    except ImportError:
        pass

def make_engine(url):
    if "sqlite" in url:
        return create_engine(url, connect_args={"check_same_thread": False})
    # For PostgreSQL / pg8000, enforce strict 2-second socket timeout to prevent serverless freeze
    return create_engine(
        url,
        connect_args={"timeout": 2.0},
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=2,
        pool_recycle=300,
    )

try:
    engine = make_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    # Emergency fallback to SQLite /tmp
    fallback_url = f"sqlite:///{tmp_db_path}" if os.path.exists(tmp_db_path) else "sqlite:///./garage.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        yield db
    except Exception as primary_err:
        if db:
            try:
                db.close()
            except Exception:
                pass
        # Fallback to local SQLite /tmp if primary PostgreSQL connection fails or times out
        try:
            fallback_url = f"sqlite:///{tmp_db_path}" if os.path.exists(tmp_db_path) else "sqlite:///./garage.db"
            fallback_engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
            FallbackSession = sessionmaker(autocommit=False, autoflush=False, bind=fallback_engine)
            fallback_db = FallbackSession()
            yield fallback_db
        finally:
            try:
                fallback_db.close()
            except Exception:
                pass
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass

