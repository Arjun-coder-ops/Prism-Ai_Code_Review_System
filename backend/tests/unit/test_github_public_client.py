import httpx
import pytest

from app.domain.pull_request_url import parse_pull_request_url
from app.integrations.github_public import GitHubPublicClient, GitHubPublicClientError


@pytest.mark.anyio
async def test_reads_public_pull_request_metadata_from_fixed_github_path() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octo-org/prism/pulls/42"
        assert request.headers["Accept"] == "application/vnd.github+json"
        return httpx.Response(
            200,
            json={
                "title": "Harden review boundary",
                "state": "open",
                "base": {
                    "sha": "base-sha",
                    "repo": {
                        "id": 123,
                        "full_name": "octo-org/prism",
                        "private": False,
                        "default_branch": "main",
                    },
                },
                "head": {"sha": "head-sha"},
            },
        )

    client = httpx.AsyncClient(
        base_url="https://api.github.com",
        transport=httpx.MockTransport(handler),
    )
    try:
        result = await GitHubPublicClient(client).get_pull_request(
            parse_pull_request_url("https://github.com/octo-org/prism/pull/42")
        )
    finally:
        await client.aclose()

    assert result.github_repository_id == 123
    assert result.head_sha == "head-sha"
    assert result.is_private is False


@pytest.mark.anyio
async def test_classifies_missing_public_pull_request_without_leaking_response(
) -> None:
    client = httpx.AsyncClient(
        base_url="https://api.github.com",
        transport=httpx.MockTransport(lambda _: httpx.Response(404)),
    )
    try:
        with pytest.raises(GitHubPublicClientError, match="pull_request_not_found"):
            await GitHubPublicClient(client).get_pull_request(
                parse_pull_request_url("https://github.com/octo-org/prism/pull/42")
            )
    finally:
        await client.aclose()
