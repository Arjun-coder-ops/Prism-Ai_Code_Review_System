import pytest

from app.domain.pull_request_url import PullRequestUrlError, parse_pull_request_url


def test_parses_canonical_public_github_pull_request_url() -> None:
    parsed = parse_pull_request_url("https://github.com/octo-org/prism/pull/42")

    assert parsed.owner == "octo-org"
    assert parsed.repository == "prism"
    assert parsed.number == 42
    assert parsed.canonical_url == "https://github.com/octo-org/prism/pull/42"


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/octo-org/prism/pull/42",
        "https://api.github.com/octo-org/prism/pull/42",
        "https://github.com@attacker.example/octo-org/prism/pull/42",
        "https://github.com/octo-org/prism/pull/42?preview=true",
        "https://github.com/octo-org/prism/pull/42#discussion",
        "https://github.com/octo-org/prism/issues/42",
        "https://github.com/octo_org/prism/pull/42",
        "https://github.com/octo-org/prism/pull/0",
    ],
)
def test_rejects_noncanonical_or_unsafe_pull_request_urls(url: str) -> None:
    with pytest.raises(PullRequestUrlError):
        parse_pull_request_url(url)
