import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.anyio
async def test_create_review_rejects_an_unsafe_url_before_service_access() -> None:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/reviews",
            json={"pull_request_url": "https://github.com@attacker.example/o/r/pull/1"},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "pull_request_url must be a canonical public GitHub pull request URL"
    )
