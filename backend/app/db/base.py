"""
SQLAlchemy engine, session factory and declarative base.

SQLite needs ``check_same_thread=False`` because FastAPI background tasks touch
the session from a different thread than the request. For PostgreSQL a small
connection pool with ``pool_pre_ping`` avoids stale-connection errors.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

if settings.is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
