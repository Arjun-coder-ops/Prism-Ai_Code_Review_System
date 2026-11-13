import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_readiness_service
from app.main import create_app
from app.services import readiness
from app.services.readiness import ComponentHealth, ReadinessService


class ReadyService(ReadinessService):
    async def check(self) -> list[ComponentHealth]:
        return [
            ComponentHealth(name="postgres", status="ok"),
            ComponentHealth(name="redis", status="ok"),
        ]


class UnreadyService(ReadinessService):
    async def check(self) -> list[ComponentHealth]:
        return [
            ComponentHealth(name="postgres", status="error", detail="unavailable"),
            ComponentHealth(name="redis", status="ok"),
        ]


class HealthyConnection:
    async def __aenter__(self) -> "HealthyConnection":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def execute(self, _: object) -> None:
        return None


class HealthyEngine:
    def connect(self) -> HealthyConnection:
        return HealthyConnection()

    async def dispose(self) -> None:
        return None


class HealthyRedis:
    async def ping(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


class FailingEngine:
    def connect(self) -> HealthyConnection:
        raise ConnectionError

    async def dispose(self) -> None:
        return None


class FailingRedis:
    async def ping(self) -> None:
        raise ConnectionError

    async def aclose(self) -> None:
        return None


@pytest.mark.anyio
async def test_ready_reports_dependencies_when_all_are_healthy() -> None:
    app = create_app()
    app.dependency_overrides[get_readiness_service] = ReadyService
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["components"] == [
        {"name": "postgres", "status": "ok", "detail": None},
        {"name": "redis", "status": "ok", "detail": None},
    ]


@pytest.mark.anyio
async def test_ready_returns_service_unavailable_when_a_dependency_fails() -> None:
    app = create_app()
    app.dependency_overrides[get_readiness_service] = UnreadyService
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


@pytest.mark.anyio
async def test_readiness_service_checks_available_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        readiness,
        "create_async_engine",
        lambda *_args, **_kwargs: HealthyEngine(),
    )
    monkeypatch.setattr(readiness.Redis, "from_url", lambda _url: HealthyRedis())

    components = await ReadinessService(
        "postgresql://prism:example@localhost/prism", "redis-url"
    ).check()

    assert components == [
        ComponentHealth(name="postgres", status="ok"),
        ComponentHealth(name="redis", status="ok"),
    ]


@pytest.mark.anyio
async def test_readiness_service_hides_dependency_connection_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        readiness,
        "create_async_engine",
        lambda *_args, **_kwargs: FailingEngine(),
    )
    monkeypatch.setattr(readiness.Redis, "from_url", lambda _url: FailingRedis())

    components = await ReadinessService(
        "postgresql://prism:example@localhost/prism", "redis-url"
    ).check()

    assert components == [
        ComponentHealth(name="postgres", status="error", detail="unavailable"),
        ComponentHealth(name="redis", status="error", detail="unavailable"),
    ]
