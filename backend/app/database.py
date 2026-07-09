# ============================================================
#  database.py — SQLAlchemy engine and session configuration
#  Business logic and model definitions live elsewhere.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

# Create the SQLAlchemy engine.
# connect_args is required only for SQLite (dev fallback).
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
)

# Each request gets its own database session via this factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM model classes inherit from this Base.
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session per request.
    Always closes the session when the request is finished."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
