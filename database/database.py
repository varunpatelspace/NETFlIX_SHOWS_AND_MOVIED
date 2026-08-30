"""
Database connection and session management module.

Provides engine configuration, connection pooling, declarative base,
and context managers for transactional session handling. Supports both
SQLite (local default) and PostgreSQL.
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)

# Determine if running SQLite or PostgreSQL
is_sqlite = DATABASE_URL.startswith("sqlite")

# SQLite requires check_same_thread=False for multi-threaded access (FastAPI / Streamlit)
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():
    """Create all database tables defined in SQLAlchemy models if they do not exist."""
    # Import models so Base registers them
    import database.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")


def reset_db():
    """Drop and recreate all database tables. Primarily used for testing or fresh re-seeding."""
    import database.models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.warning("Database tables dropped and recreated.")


def seed_database_if_empty():
    """
    Safely seed the database with initial catalog records if the database is empty.
    
    Protects existing databases: if records already exist, execution is immediately
    skipped with zero modification.
    """
    from config.settings import AUTO_SEED_DB, DATA_SOURCE_PATH
    if not AUTO_SEED_DB:
        logger.info("Database auto-seeding disabled via AUTO_SEED_DB=false.")
        return

    import os
    from database.repository import NetflixRepository

    with get_db_context() as db:
        repo = NetflixRepository(db)
        count = repo.get_total_count()
        if count > 0:
            logger.info(f"Database already populated ({count:,} records). Skipping auto-seed.")
            return

        logger.info("Database is empty. Checking seed dataset availability...")
        if not os.path.exists(DATA_SOURCE_PATH):
            logger.warning(f"Seed dataset not found at '{DATA_SOURCE_PATH}'. Starting with empty database.")
            return

        logger.info(f"Auto-seeding database from '{DATA_SOURCE_PATH}'...")
        try:
            from pipeline.pipeline_runner import run_pipeline
            report = run_pipeline(
                source_type="csv",
                source_path=DATA_SOURCE_PATH,
                db_session=db,
                mode="insert_new_only"
            )
            logger.info(
                f"Auto-seeding complete: status={report.get('final_status')}, "
                f"inserted={report.get('incremental_metrics', {}).get('inserted', 0)}"
            )
        except Exception as e:
            logger.error(f"Auto-seeding failed: {e}", exc_info=True)



@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic commit/rollback and cleanup.
    
    Usage:
        with get_db_context() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection provider for database sessions.
    
    Yields:
        Session: Active SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
