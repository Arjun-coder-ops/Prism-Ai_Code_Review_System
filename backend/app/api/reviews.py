from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.pull_request_url import PullRequestUrlError, parse_pull_request_url
from app.integrations.github_public import GitHubPublicClientError
from app.schemas.review import AcceptedReviewResponse, CreateReviewRequest
from app.services.review_intake import ReviewIntakeService

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
