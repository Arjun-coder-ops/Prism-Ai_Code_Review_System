from dataclasses import dataclass
from typing import Any

import httpx

from app.domain.pull_request_url import ParsedPullRequestUrl

_GITHUB_API_BASE_URL = "https://api.github.com"
_GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}


class GitHubPublicClientError(RuntimeError):
    """A safe, classified GitHub API failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class PublicPullRequest:
    github_repository_id: int
    owner: str
    repository: str
    full_name: str
    is_private: bool
    default_branch: str
    number: int
    title: str
    state: str
    base_sha: str
    head_sha: str


class GitHubPublicClient:
    """Read public pull-request metadata without following untrusted URLs."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=_GITHUB_API_BASE_URL,
            follow_redirects=False,
            headers=_GITHUB_HEADERS,
            timeout=httpx.Timeout(10.0),
        )
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_pull_request(
        self, parsed_url: ParsedPullRequestUrl
    ) -> PublicPullRequest:
        path = (
            f"/repos/{parsed_url.owner}/{parsed_url.repository}/pulls/"
            f"{parsed_url.number}"
        )
        try:
            response = await self._client.get(path, headers=_GITHUB_HEADERS)
        except httpx.HTTPError as exc:
            raise GitHubPublicClientError("upstream_unavailable") from exc

        if response.status_code == 404:
            raise GitHubPublicClientError("pull_request_not_found")
        if response.status_code != 200:
            raise GitHubPublicClientError("upstream_unavailable")

        try:
            payload = response.json()
            return _parse_pull_request_payload(payload, parsed_url)
        except (TypeError, ValueError, KeyError) as exc:
            raise GitHubPublicClientError("invalid_upstream_response") from exc


def _parse_pull_request_payload(
    payload: Any,
    requested_url: ParsedPullRequestUrl,
) -> PublicPullRequest:
    if not isinstance(payload, dict):
        raise ValueError("expected an object")

    base = payload["base"]
    head = payload["head"]
    repository = base["repo"]
    if not isinstance(base, dict) or not isinstance(head, dict):
        raise ValueError("missing pull request refs")
    if not isinstance(repository, dict):
        raise ValueError("missing repository")

    github_repository_id = repository["id"]
    full_name = repository["full_name"]
    title = payload["title"]
    state = payload["state"]
    base_sha = base["sha"]
    head_sha = head["sha"]
    default_branch = repository["default_branch"]
    is_private = repository["private"]
    if not (
        isinstance(github_repository_id, int)
        and isinstance(full_name, str)
        and isinstance(title, str)
        and isinstance(state, str)
        and isinstance(base_sha, str)
        and isinstance(head_sha, str)
        and isinstance(default_branch, str)
        and isinstance(is_private, bool)
        and full_name == f"{requested_url.owner}/{requested_url.repository}"
    ):
        raise ValueError("invalid pull request metadata")

    return PublicPullRequest(
        github_repository_id=github_repository_id,
        owner=requested_url.owner,
        repository=requested_url.repository,
        full_name=full_name,
        is_private=is_private,
        default_branch=default_branch,
        number=requested_url.number,
        title=title,
        state=state,
        base_sha=base_sha,
        head_sha=head_sha,
    )
