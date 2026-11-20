"""
Database session and connection management.
Optimized for high-concurrency SQLite (WAL mode) and production PostgreSQL.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings
from src.db.models import Base

# Engine configuration
raw_db_url = settings.db_url
# Normalize URL prefix for psycopg2 driver (SQLAlchemy 2.x uses psycopg3 by default for postgresql://)
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif raw_db_url.startswith("postgresql://"):
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine_kwargs = {"echo": False}
if raw_db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30.0}

engine = create_engine(raw_db_url, **engine_kwargs)

# Enable SQLite Write-Ahead Logging (WAL) and foreign keys for high-concurrency crash safety
if raw_db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes schema and tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic commit/rollback."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
