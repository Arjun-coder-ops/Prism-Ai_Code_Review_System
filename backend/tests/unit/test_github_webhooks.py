import hashlib
import hmac

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


def _signature(payload: bytes, secret: str = "test-secret") -> str:
    return "sha256=" + hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()


@pytest.mark.anyio
async def test_webhook_rejects_requests_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    get_settings.cache_clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=create_app()), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/github/webhooks", content=b"{}")
        assert response.status_code == 503
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_webhook_rejects_an_invalid_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    get_settings.cache_clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=create_app()), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/github/webhooks",
                content=b'{"zen":"test"}',
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": "sha256=incorrect",
                },
            )
        assert response.status_code == 401
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_webhook_accepts_a_valid_signed_supported_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b'{"zen":"test"}'
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    get_settings.cache_clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=create_app()), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/github/webhooks",
                content=payload,
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": _signature(payload),
                },
            )
        assert response.status_code == 202
        assert response.json() == {"status": "accepted"}
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_webhook_ignores_an_unknown_signed_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"{}"
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    get_settings.cache_clear()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=create_app()), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/github/webhooks",
                content=payload,
                headers={
                    "X-GitHub-Event": "unrecognized",
                    "X-Hub-Signature-256": _signature(payload),
                },
            )
        assert response.status_code == 202
        assert response.json() == {"status": "ignored"}
    finally:
        get_settings.cache_clear()
