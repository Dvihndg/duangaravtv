import os
from sqlalchemy import create_engine
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

# ─── Engine Configuration ──────────────────────────────────────────────────────
is_sqlite = "sqlite" in db_url

if is_sqlite:
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)
else:
    # PostgreSQL (Supabase / Neon / Railway): Serverless-optimized pool settings
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
