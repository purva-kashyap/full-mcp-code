"""Reusable PostgreSQL configuration and SQLAlchemy engine helpers"""
import threading
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import config
from .exceptions import ValidationError


def get_db_config() -> dict[str, Any]:
    """Return normalized PostgreSQL config values for reuse."""
    return {
        "dsn": (config.POSTGRES_DSN or "").strip(),
        "host": config.POSTGRES_HOST,
        "port": config.POSTGRES_PORT,
        "database": config.POSTGRES_DB,
        "username": config.POSTGRES_USER,
        "password": config.POSTGRES_PASSWORD,
        "sslmode": config.POSTGRES_SSLMODE,
    }


def get_postgres_url(db_config: dict[str, Any] | None = None) -> str:
    """Build PostgreSQL SQLAlchemy URL from provided or environment config."""
    resolved_config = db_config or get_db_config()

    dsn = str(resolved_config.get("dsn", "")).strip()
    if dsn:
        if dsn.startswith("postgresql://") or dsn.startswith("postgresql+"):
            return dsn
        raise ValidationError(
            "POSTGRES_DSN must be a SQLAlchemy/PostgreSQL URL (e.g. postgresql+asyncpg://user:pass@host:5432/dbname)",
            details={"POSTGRES_DSN": "invalid format"},
        )

    required_values = {
        "POSTGRES_HOST": resolved_config.get("host"),
        "POSTGRES_DB": resolved_config.get("database"),
        "POSTGRES_USER": resolved_config.get("username"),
        "POSTGRES_PASSWORD": resolved_config.get("password"),
    }
    missing = [key for key, value in required_values.items() if not value]
    if missing:
        raise ValidationError(
            "PostgreSQL configuration is missing. Set POSTGRES_DSN or individual POSTGRES_* variables.",
            details={"missing": missing},
        )

    return URL.create(
        drivername="postgresql+asyncpg",
        username=resolved_config["username"],
        password=resolved_config["password"],
        host=resolved_config["host"],
        port=int(resolved_config.get("port", 5432)),
        database=resolved_config["database"],
        query={"sslmode": str(resolved_config.get("sslmode", "prefer"))},
    ).render_as_string(hide_password=False)


_async_db_engine: AsyncEngine | None = None
_async_db_engine_lock = threading.Lock()
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_db_engine(db_url: str | None = None) -> AsyncEngine:
    """Get or create global async SQLAlchemy engine for PostgreSQL."""
    global _async_db_engine
    if _async_db_engine is None:
        with _async_db_engine_lock:
            if _async_db_engine is None:
                _async_db_engine = create_async_engine(
                    db_url or get_postgres_url(),
                    pool_pre_ping=True,
                    pool_size=config.POSTGRES_POOL_SIZE,
                    max_overflow=config.POSTGRES_MAX_OVERFLOW,
                    pool_timeout=config.POSTGRES_POOL_TIMEOUT,
                    pool_recycle=config.POSTGRES_POOL_RECYCLE,
                    connect_args={
                        "server_settings": {
                            "application_name": "mcp_server",
                        },
                        "timeout": config.POSTGRES_CONNECT_TIMEOUT,
                        "command_timeout": config.POSTGRES_COMMAND_TIMEOUT,
                    },
                    echo=False,
                )
    return _async_db_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create global async SQLAlchemy session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        with _async_db_engine_lock:
            if _async_session_factory is None:
                _async_session_factory = async_sessionmaker(
                    bind=get_async_db_engine(),
                    expire_on_commit=False,
                    autoflush=False,
                )
    return _async_session_factory


@asynccontextmanager
async def get_async_session():
    """Yield an AsyncSession from the global session factory."""
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        yield session


async def close_async_db_engine() -> None:
    """Dispose global async DB engine during graceful shutdown."""
    global _async_db_engine
    global _async_session_factory
    _async_session_factory = None

    if _async_db_engine is not None:
        await _async_db_engine.dispose()
        _async_db_engine = None
