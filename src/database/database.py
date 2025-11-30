import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import Pool

from .models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None 

def init_db(database_url: str, echo: bool = False):
    """
    Initialize database engine and session factory.
    """
    global _engine, _session_factory

    logger.info(f"Initializing database connection: {database_url.split('://')[0]}://...")

    # SQLite-specific configuration
    connect_args = {}
    if "sqlite" in database_url:
        # Enable foreign keys for SQLite (required for CASCADE to work)
        connect_args = {"check_same_thread": False}

    _engine = create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        pool_recycle=3600, # Recycle connections after 1 hour
        connect_args=connect_args,
    )

    # Enable foreign keys for SQLite
    if "sqlite" in database_url:
        @event.listens_for(_engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        logger.info("SQLite foreign keys enabled")

    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,  # Changed to True to ensure data is flushed before commit
    )

    logger.info("Database connection initialized successfully")


async def create_tables():
    """
    Create all database tables.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    logger.info("Creating database tables ")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def drop_tables():
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables dropped")


@asynccontextmanager
async def get_session():
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    session = _session_factory()
    try:
        logger.debug("Session started")
        yield session
        await session.commit()
        logger.debug("Session committed successfully")
    except Exception as e:
        logger.error(f"Session error, rolling back: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()
        logger.debug("Session closed")

async def close_db():
    """
    Close database connection.
    """
    global _engine, _session_factory

    if _engine is not None:
        logger.info("Closing database connection...")
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection closed")