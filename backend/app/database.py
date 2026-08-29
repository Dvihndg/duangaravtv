import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ─── Database URL Resolution ──────────────────────────────────────────────────
# Priority: Environment Variable → Config file → SQLite fallback
db_url = os.getenv("DATABASE_URL", "sqlite:///./garage.db")

# Fix: Supabase/Heroku uses "postgres://" but SQLAlchemy 2.x requires "postgresql://"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# ─── Engine Configuration ──────────────────────────────────────────────────────
is_sqlite = "sqlite" in db_url

if is_sqlite:
    # SQLite: simple local dev setup
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)
else:
    # PostgreSQL (Supabase / Neon / Railway): Serverless-optimized pool settings
    # pool_pre_ping: test connection before use (handles idle connection drops)
    # pool_size + max_overflow: limit connections for serverless concurrency
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,  # recycle connections every 5 minutes
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
