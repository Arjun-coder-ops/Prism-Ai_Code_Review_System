import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.db.session import SessionLocal, engine
from app.integrations.github_public import (
    GitHubPublicClientError,
    PublicPullRequestFile,
)
from app.models.review import PullRequest, Repository, ReviewFinding, ReviewRun
from app.services import review_processor
from app.services.review_processor import (
    RetryableReviewProcessingError,
    process_review_run,
)


class DeterministicFileClient:
    async def list_pull_request_files(
        self, _: object
    ) -> list[PublicPullRequestFile]:
        return [
            PublicPullRequestFile(
                path="src/example.py",
                status="modified",
                patch="@@ -1,1 +1,2 @@\n safe = True\n+eval(request_body)\n",
            )
        ]

    async def aclose(self) -> None:
        return None


class FailingFileClient:
    def __init__(self, code: str) -> None:
        self._code = code

    async def list_pull_request_files(self, _: object) -> list[PublicPullRequestFile]:
        raise GitHubPublicClientError(self._code)

    async def aclose(self) -> None:
        return None


@pytest.fixture(autouse=True)
async def dispose_database_pool_after_test() -> None:
    """Avoid carrying asyncpg connections into pytest's next event loop."""
    yield
    await engine.dispose()


async def _create_review_run(*, status: str = "queued") -> uuid.UUID:
    unique = uuid.uuid4()
    async with SessionLocal() as session:
        repository = Repository(
            github_repository_id=unique.int % 2_000_000_000,
            owner="prism-test",
            name=str(unique),
            full_name=f"prism-test/{unique}",
            is_private=False,
            default_branch="main",
        )
        session.add(repository)
        await session.flush()
        pull_request = PullRequest(
            repository_id=repository.id,
            github_pr_number=1,
            title="Test review",
            base_sha="a" * 40,
            current_head_sha="b" * 40,
            state="open",
        )
        session.add(pull_request)
        await session.flush()
        review_run = ReviewRun(
            pull_request_id=pull_request.id,
            reviewed_head_sha="b" * 40,
            review_policy_version="deterministic-v1",
            status=status,
            started_at=(
                datetime.now(UTC) - timedelta(minutes=11)
                if status == "static_analyzing"
                else None
            ),
        )
        session.add(review_run)
        await session.commit()
        return review_run.id


async def _cleanup_review_run(review_run_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        run = await session.get(ReviewRun, review_run_id)
        if run is None:
            return
        pull_request_id = run.pull_request_id
        pull_request = await session.get(PullRequest, pull_request_id)
        repository_id = pull_request.repository_id if pull_request else None
        await session.execute(
            delete(ReviewFinding).where(ReviewFinding.review_run_id == review_run_id)
        )
        await session.execute(delete(ReviewRun).where(ReviewRun.id == review_run_id))
        await session.execute(
            delete(PullRequest).where(PullRequest.id == pull_request_id)
        )
        if repository_id is not None:
            await session.execute(
                delete(Repository).where(Repository.id == repository_id)
            )
        await session.commit()


@pytest.mark.anyio
@pytest.mark.integration
async def test_processor_persists_verified_finding_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_run_id = await _create_review_run()
    monkeypatch.setattr(review_processor, "GitHubPublicClient", DeterministicFileClient)
    try:
        assert await process_review_run(review_run_id) == "completed"
        assert await process_review_run(review_run_id) == "completed"
        async with SessionLocal() as session:
            review_run = await session.get(ReviewRun, review_run_id)
            findings = list(
                (
                    await session.execute(
                        select(ReviewFinding).where(
                            ReviewFinding.review_run_id == review_run_id
                        )
                    )
                ).scalars()
            )
        assert review_run is not None
        assert review_run.status == "completed"
        assert len(findings) == 1
        assert findings[0].evidence["line"] == 2
    finally:
        await _cleanup_review_run(review_run_id)


@pytest.mark.anyio
@pytest.mark.integration
async def test_processor_prevents_duplicate_concurrent_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_run_id = await _create_review_run()
    monkeypatch.setattr(review_processor, "GitHubPublicClient", DeterministicFileClient)
    try:
        results = await asyncio.gather(
            process_review_run(review_run_id),
            process_review_run(review_run_id),
        )
        assert "completed" in results
        assert all(result in {"completed", "in_progress"} for result in results)
        async with SessionLocal() as session:
            findings = list(
                (
                    await session.execute(
                        select(ReviewFinding).where(
                            ReviewFinding.review_run_id == review_run_id
                        )
                    )
                ).scalars()
            )
        assert len(findings) == 1
    finally:
        await _cleanup_review_run(review_run_id)


@pytest.mark.anyio
@pytest.mark.integration
async def test_processor_recovers_a_stale_worker_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_run_id = await _create_review_run(status="static_analyzing")
    monkeypatch.setattr(review_processor, "GitHubPublicClient", DeterministicFileClient)
    try:
        assert await process_review_run(review_run_id) == "completed"
    finally:
        await _cleanup_review_run(review_run_id)


@pytest.mark.anyio
@pytest.mark.integration
async def test_processor_marks_permanent_upstream_failures_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_run_id = await _create_review_run()
    monkeypatch.setattr(
        review_processor,
        "GitHubPublicClient",
        lambda: FailingFileClient("too_many_changed_files"),
    )
    try:
        assert await process_review_run(review_run_id) == "failed"
        async with SessionLocal() as session:
            review_run = await session.get(ReviewRun, review_run_id)
        assert review_run is not None
        assert review_run.status == "failed"
        assert review_run.failure_reason == "too_many_changed_files"
    finally:
        await _cleanup_review_run(review_run_id)


@pytest.mark.anyio
@pytest.mark.integration
async def test_processor_retries_transient_upstream_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_run_id = await _create_review_run()
    monkeypatch.setattr(
        review_processor,
        "GitHubPublicClient",
        lambda: FailingFileClient("upstream_unavailable"),
    )
    try:
        with pytest.raises(RetryableReviewProcessingError):
            await process_review_run(review_run_id)
    finally:
        await _cleanup_review_run(review_run_id)
