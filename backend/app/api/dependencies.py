from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.integrations.github_public import GitHubPublicClient
from app.services.readiness import ReadinessService
from app.services.review_intake import ReviewIntakeService


def get_readiness_service() -> ReadinessService:
    settings = get_settings()
    return ReadinessService(
        database_url=settings.database_url,
        redis_url=settings.redis_url,
        database_connect_timeout=settings.database_connect_timeout,
    )


async def get_github_public_client() -> AsyncGenerator[GitHubPublicClient, None]:
    client = GitHubPublicClient()
    try:
        yield client
    finally:
        await client.aclose()


async def get_review_intake_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    github_client: Annotated[GitHubPublicClient, Depends(get_github_public_client)],
) -> ReviewIntakeService:
    return ReviewIntakeService(session, github_client)
