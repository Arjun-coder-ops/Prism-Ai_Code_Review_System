import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.domain.pull_request_url import PullRequestUrlError, parse_pull_request_url
from app.integrations.github_public import GitHubPublicClientError
from app.schemas.review import (
    AcceptedReviewResponse,
    CreateReviewRequest,
    FindingResponse,
    ReviewStatusResponse,
)
from app.services.review_intake import ReviewIntakeService
from app.services.review_results import get_review_result

from .dependencies import get_review_intake_service

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

ReviewIntakeDependency = Annotated[
    ReviewIntakeService,
    Depends(get_review_intake_service),
]


@router.post(
    "",
    response_model=AcceptedReviewResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_review(
    request: CreateReviewRequest,
    intake_service: ReviewIntakeDependency,
) -> AcceptedReviewResponse:
    """Queue a review of a validated public GitHub pull request."""
    try:
        parsed_url = parse_pull_request_url(request.pull_request_url)
    except PullRequestUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "pull_request_url must be a canonical public GitHub pull request URL"
            ),
        ) from exc

    try:
        review = await intake_service.accept(parsed_url)
    except GitHubPublicClientError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if exc.code == "pull_request_not_found"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(
            status_code=status_code,
            detail="pull request metadata is unavailable",
        ) from exc

    return AcceptedReviewResponse(
        id=review.review_id,
        status="queued",
        head_sha=review.head_sha,
    )


@router.get("/{review_id}", response_model=ReviewStatusResponse)
async def get_review(
    review_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReviewStatusResponse:
    try:
        parsed_id = uuid.UUID(review_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    result = await get_review_result(session, parsed_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    review_run, findings = result
    return ReviewStatusResponse(
        id=str(review_run.id),
        status=review_run.status,
        head_sha=review_run.reviewed_head_sha,
        findings=[
            FindingResponse(
                file_path=finding.file_path,
                start_line=finding.start_line,
                end_line=finding.end_line,
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                explanation=finding.explanation,
                evidence=finding.evidence,
                verification_status=finding.verification_status,
            )
            for finding in findings
        ],
    )
