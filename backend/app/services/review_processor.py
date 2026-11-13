import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.pipeline import analyze_patched_files
from app.db.session import SessionLocal
from app.domain.pull_request_url import ParsedPullRequestUrl
from app.integrations.github_public import GitHubPublicClient, GitHubPublicClientError
from app.models.review import PullRequest, Repository, ReviewFinding, ReviewRun


class RetryableReviewProcessingError(RuntimeError):
    """The worker may safely retry an upstream GitHub failure."""


_ACTIVE_STATUSES = ("static_analyzing", "verifying")
_CLAIMABLE_STATUSES = ("queued", "failed")
_PROCESSING_LEASE_SECONDS = 600


async def _claim_review_run(
    session: AsyncSession,
    review_run_id: uuid.UUID,
) -> bool:
    """Claim a run once, or recover an abandoned worker lease.

    The conditional update is the concurrency boundary: duplicate broker
    deliveries cannot both transition the same run into active processing.
    Celery's hard time limit is below the lease, so a live task retains its
    claim while an interrupted task becomes eligible for recovery.
    """
    claimed_at = datetime.now(UTC)
    stale_before = claimed_at - timedelta(seconds=_PROCESSING_LEASE_SECONDS)
    result = await session.execute(
        update(ReviewRun)
        .where(
            ReviewRun.id == review_run_id,
            or_(
                ReviewRun.status.in_(_CLAIMABLE_STATUSES),
                and_(
                    ReviewRun.status.in_(_ACTIVE_STATUSES),
                    ReviewRun.started_at.is_not(None),
                    ReviewRun.started_at < stale_before,
                ),
            ),
        )
        .values(
            status="static_analyzing",
            started_at=claimed_at,
            finished_at=None,
            failure_reason=None,
        )
        .returning(ReviewRun.id)
    )
    return result.scalar_one_or_none() is not None


async def process_review_run(review_run_id: uuid.UUID) -> str:
    """Persist deterministic findings for one review ID without executing source."""
    async with SessionLocal() as session:
        claimed = await _claim_review_run(session, review_run_id)
        await session.commit()
        if not claimed:
            existing = await session.get(ReviewRun, review_run_id)
            if existing is None:
                return "missing"
            if existing.status == "completed":
                return "completed"
            return "in_progress"

        result = await session.execute(
            select(ReviewRun, PullRequest, Repository)
            .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(ReviewRun.id == review_run_id)
        )
        row = result.one_or_none()
        # Defensive guard for a record deleted after its durable claim.
        if row is None:
            return "missing"
        review_run, pull_request, repository = row
        await session.execute(
            delete(ReviewFinding).where(ReviewFinding.review_run_id == review_run.id)
        )
        await session.commit()

        client = GitHubPublicClient()
        try:
            files = await client.list_pull_request_files(
                ParsedPullRequestUrl(
                    owner=repository.owner,
                    repository=repository.name,
                    number=pull_request.github_pr_number,
                )
            )
        except GitHubPublicClientError as exc:
            review_run.status = "failed"
            review_run.failure_reason = exc.code
            review_run.finished_at = datetime.now(UTC)
            await session.commit()
            if exc.code == "upstream_unavailable":
                raise RetryableReviewProcessingError from exc
            return "failed"
        finally:
            await client.aclose()

        review_run.status = "verifying"
        await session.commit()
        for candidate in analyze_patched_files(files):
            session.add(
                ReviewFinding(
                    review_run_id=review_run.id,
                    file_path=candidate.file_path,
                    start_line=candidate.line_number,
                    end_line=candidate.line_number,
                    category=candidate.category,
                    severity=candidate.severity,
                    confidence=1.0,
                    title=candidate.title,
                    explanation=candidate.explanation,
                    evidence={
                        "source": "github_patch",
                        "head_sha": review_run.reviewed_head_sha,
                        "line": candidate.line_number,
                        "snippet": candidate.evidence,
                    },
                    impact="Requires human review; no exploitability is asserted.",
                    recommendation="Avoid dynamic execution of untrusted input.",
                    verification_status="verified",
                )
            )
        review_run.status = "completed"
        review_run.failure_reason = None
        review_run.finished_at = datetime.now(UTC)
        await session.commit()
        return "completed"
