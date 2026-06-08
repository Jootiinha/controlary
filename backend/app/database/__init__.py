"""Database module initialization."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

# Create declarative base for ORM models
Base = declarative_base()

# Database engine will be initialized in app factory
engine = None
SessionLocal = None


def init_db(database_url: str, echo: bool = False):
    """Initialize database engine and session factory."""
    global engine, SessionLocal

    # Determine if using SQLite
    is_sqlite = database_url.startswith("sqlite")

    connect_args = {}
    poolclass = None

    if is_sqlite:
        # SQLite requires check_same_thread=False for multi-threading
        connect_args = {"check_same_thread": False}
        # Use StaticPool for testing
        if "test" in database_url or ":memory:" in database_url:
            poolclass = StaticPool

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        poolclass=poolclass,
        echo=echo,
    )

    # Enable foreign keys for SQLite
    if is_sqlite:
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    return engine, SessionLocal


def get_db():
    """Get database session (dependency for FastAPI)."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Create all tables in the database."""
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    Base.metadata.create_all(bind=engine)
