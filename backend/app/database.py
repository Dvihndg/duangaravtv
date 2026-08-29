import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ─── Database URL Resolution ──────────────────────────────────────────────────
db_url = os.getenv("DATABASE_URL", "sqlite:///./garage.db")

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
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=10,
        pool_recycle=300,
    )

try:
    engine = make_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    # Emergency fallback to SQLite /tmp
    tmp_url = "sqlite:////tmp/garage.db"
    engine = create_engine(tmp_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    try:
        db = SessionLocal()
        # Ping connection
        db.execute(text("SELECT 1"))
        try:
            yield db
        finally:
            db.close()
    except Exception as primary_err:
        # Fallback to local SQLite /tmp if primary PostgreSQL connection fails
        try:
            fallback_url = "sqlite:////tmp/garage.db"
            fallback_engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
            Base.metadata.create_all(bind=fallback_engine)
            FallbackSession = sessionmaker(autocommit=False, autoflush=False, bind=fallback_engine)
            db = FallbackSession()
            yield db
        finally:
            db.close()
