from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_session
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


@pytest.mark.anyio
async def test_get_review_rejects_an_invalid_identifier() -> None:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/reviews/not-a-uuid")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_review_returns_persisted_verified_findings() -> None:
    review_id = "2ed5f15e-fa09-4ce8-bcd1-d7d4ea2cdd10"
    finding = SimpleNamespace(
        file_path="src/example.py",
        start_line=8,
        end_line=8,
        category="security",
        severity="high",
        title="Dynamic code execution",
        explanation="The added code evaluates untrusted input.",
        evidence={"source": "github_patch", "line": 8},
        verification_status="verified",
    )

    class ScalarResult:
        def scalars(self) -> list[SimpleNamespace]:
            return [finding]

    class Session:
        async def get(self, _: object, identifier: object) -> SimpleNamespace | None:
            if str(identifier) != review_id:
                return None
            return SimpleNamespace(
                id=review_id,
                status="completed",
                reviewed_head_sha="abc123",
            )

        async def execute(self, _: object) -> ScalarResult:
            return ScalarResult()

    async def override_session():
        yield Session()

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/api/v1/reviews/{review_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": review_id,
        "status": "completed",
        "head_sha": "abc123",
        "findings": [
            {
                "file_path": "src/example.py",
                "start_line": 8,
                "end_line": 8,
                "category": "security",
                "severity": "high",
                "title": "Dynamic code execution",
                "explanation": "The added code evaluates untrusted input.",
                "evidence": {"source": "github_patch", "line": 8},
                "verification_status": "verified",
            }
        ],
    }
