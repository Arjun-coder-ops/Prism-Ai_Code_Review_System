import asyncio
from dataclasses import dataclass
from typing import Literal

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.engine import normalize_async_database_url

ComponentName = Literal["postgres", "redis"]
ComponentStatus = Literal["ok", "error"]


@dataclass(frozen=True)
class ComponentHealth:
    name: ComponentName
    status: ComponentStatus
    detail: str | None = None


class ReadinessService:
    """Checks configured infrastructure without disclosing connection details."""

    def __init__(
        self,
        database_url: str = "",
        redis_url: str = "",
        database_connect_timeout: float = 10.0,
    ) -> None:
        self._database_url = database_url
        self._redis_url = redis_url
        self._database_connect_timeout = database_connect_timeout

    async def check(self) -> list[ComponentHealth]:
        return list(
            await asyncio.gather(
                self._check_postgres(),
                self._check_redis(),
            )
        )

    async def _check_postgres(self) -> ComponentHealth:
        engine = None
        try:
            target = normalize_async_database_url(self._database_url)
            engine = create_async_engine(
                target.url,
                connect_args={
                    **target.connect_args,
                    "timeout": self._database_connect_timeout,
                },
                pool_pre_ping=True,
            )
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return ComponentHealth(
                name="postgres",
                status="error",
                detail="unavailable",
            )
        finally:
            if engine is not None:
                await engine.dispose()
        return ComponentHealth(name="postgres", status="ok")

    async def _check_redis(self) -> ComponentHealth:
        client = Redis.from_url(self._redis_url)
        try:
            await client.ping()
        except Exception:
            return ComponentHealth(name="redis", status="error", detail="unavailable")
        finally:
            await client.aclose()
        return ComponentHealth(name="redis", status="ok")
