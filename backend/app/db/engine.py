from dataclasses import dataclass
from typing import Any

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings


@dataclass(frozen=True)
class AsyncDatabaseTarget:
    url: URL
    connect_args: dict[str, Any]


def normalize_async_database_url(database_url: str) -> AsyncDatabaseTarget:
    """Adapt libpq-style PostgreSQL URLs for SQLAlchemy's asyncpg dialect.

    Neon provides `sslmode` and `channel_binding` query arguments intended for
    libpq clients. asyncpg rejects those names, so TLS is supplied through its
    supported `ssl` connect argument instead.
    """
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        raise ValueError("DATABASE_URL must use a PostgreSQL scheme")

    query = dict(parsed.query)
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    ssl = query.pop("ssl", None)
    hostname = parsed.host or ""
    requires_tls = hostname.endswith(".neon.tech") or sslmode is not None
    connect_args: dict[str, Any] = {}
    if requires_tls:
        connect_args["ssl"] = ssl or "require"

    return AsyncDatabaseTarget(
        url=parsed.set(drivername="postgresql+asyncpg", query=query),
        connect_args=connect_args,
    )


def create_database_engine(
    settings: Settings, *, migration: bool = False
) -> AsyncEngine:
    """Create a short-lived-safe async engine without connecting at import time."""
    source_url = settings.migration_database_url if migration else settings.database_url
    target = normalize_async_database_url(source_url)
    return create_async_engine(
        target.url,
        connect_args={
            **target.connect_args,
            "timeout": settings.database_connect_timeout,
        },
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_pool_size,
    )
