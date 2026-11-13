from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.pull_request_url import ParsedPullRequestUrl
from app.integrations.github_public import GitHubPublicClient, PublicPullRequest
from app.models.review import PullRequest, Repository, ReviewRun
from app.services.review_dispatcher import ReviewDispatcher

_REVIEW_POLICY_VERSION = "deterministic-v1"


@dataclass(frozen=True)
class AcceptedReview:
    review_id: str
    status: str
    head_sha: str


class ReviewIntakeService:
    """Persist idempotent review work only after GitHub metadata validates it."""

    def __init__(
        self,
        session: AsyncSession,
        github_client: GitHubPublicClient,
        dispatcher: ReviewDispatcher,
    ) -> None:
        self._session = session
        self._github_client = github_client
        self._dispatcher = dispatcher

    async def accept(self, parsed_url: ParsedPullRequestUrl) -> AcceptedReview:
        source_pull_request = await self._github_client.get_pull_request(parsed_url)
        repository = await self._get_or_create_repository(source_pull_request)
        pull_request = await self._get_or_create_pull_request(
            repository,
            source_pull_request,
        )
        review_run = await self._get_or_create_review_run(
            pull_request,
            source_pull_request.head_sha,
        )
        await self._session.commit()
        if review_run.status == "queued":
            self._dispatcher.enqueue(str(review_run.id))
        return AcceptedReview(
            review_id=str(review_run.id),
            status=review_run.status,
            head_sha=review_run.reviewed_head_sha,
        )

    async def _get_or_create_repository(self, source: PublicPullRequest) -> Repository:
        github_repository_id = source.github_repository_id
        result = await self._session.execute(
            select(Repository).where(
                Repository.github_repository_id == github_repository_id
            )
        )
        repository = result.scalar_one_or_none()
        if repository is None:
            repository = Repository(
                github_repository_id=github_repository_id,
                owner=source.owner,
                name=source.repository,
                full_name=source.full_name,
                is_private=source.is_private,
                default_branch=source.default_branch,
            )
            self._session.add(repository)
            await self._session.flush()
        return repository

    async def _get_or_create_pull_request(
        self,
        repository: Repository,
        source: PublicPullRequest,
    ) -> PullRequest:
        github_pr_number = source.number
        result = await self._session.execute(
            select(PullRequest).where(
                PullRequest.repository_id == repository.id,
                PullRequest.github_pr_number == github_pr_number,
            )
        )
        pull_request = result.scalar_one_or_none()
        if pull_request is None:
            pull_request = PullRequest(
                repository_id=repository.id,
                github_pr_number=github_pr_number,
                title=source.title,
                base_sha=source.base_sha,
                current_head_sha=source.head_sha,
                state=source.state,
            )
            self._session.add(pull_request)
            await self._session.flush()
        else:
            pull_request.title = source.title
            pull_request.base_sha = source.base_sha
            pull_request.current_head_sha = source.head_sha
            pull_request.state = source.state
        return pull_request

    async def _get_or_create_review_run(
        self,
        pull_request: PullRequest,
        head_sha: str,
    ) -> ReviewRun:
        result = await self._session.execute(
            select(ReviewRun).where(
                ReviewRun.pull_request_id == pull_request.id,
                ReviewRun.reviewed_head_sha == head_sha,
                ReviewRun.review_policy_version == _REVIEW_POLICY_VERSION,
            )
        )
        review_run = result.scalar_one_or_none()
        if review_run is None:
            review_run = ReviewRun(
                pull_request_id=pull_request.id,
                reviewed_head_sha=head_sha,
                review_policy_version=_REVIEW_POLICY_VERSION,
                status="queued",
            )
            self._session.add(review_run)
            await self._session.flush()
        return review_run
