# ============================================================
#  database.py — SQLAlchemy engine and session configuration
#  Business logic and model definitions live elsewhere.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
)

# Each request gets its own database session via this factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM model classes inherit from this Base.
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session per request.
    Logs and rolls back active transactions on exception, always closing when finished."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
