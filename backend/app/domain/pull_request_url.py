from dataclasses import dataclass
from urllib.parse import urlparse

_GITHUB_HOST = "github.com"
_IDENTIFIER_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
)


class PullRequestUrlError(ValueError):
    """Raised when a URL is not a canonical public GitHub pull request URL."""


@dataclass(frozen=True)
class ParsedPullRequestUrl:
    owner: str
    repository: str
    number: int

    @property
    def canonical_url(self) -> str:
        return f"https://{_GITHUB_HOST}/{self.owner}/{self.repository}/pull/{self.number}"


def _is_github_identifier(value: str) -> bool:
    return (
        1 <= len(value) <= 100
        and value[0] != "-"
        and value[-1] != "-"
        and all(character in _IDENTIFIER_CHARACTERS for character in value)
    )


def parse_pull_request_url(value: str) -> ParsedPullRequestUrl:
    """Parse one canonical GitHub pull-request URL without accessing the network."""
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != _GITHUB_HOST
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise PullRequestUrlError(
            "URL must be a canonical https://github.com pull request"
        )

    path_parts = parsed.path.split("/")
    if len(path_parts) != 5 or path_parts[0] != "" or path_parts[3] != "pull":
        raise PullRequestUrlError("URL must use /{owner}/{repository}/pull/{number}")

    owner, repository, number_text = path_parts[1], path_parts[2], path_parts[4]
    if not _is_github_identifier(owner) or not _is_github_identifier(repository):
        raise PullRequestUrlError("GitHub owner and repository names are invalid")
    if not number_text.isdecimal() or int(number_text) < 1:
        raise PullRequestUrlError("Pull request number must be a positive integer")

    return ParsedPullRequestUrl(
        owner=owner,
        repository=repository,
        number=int(number_text),
    )
