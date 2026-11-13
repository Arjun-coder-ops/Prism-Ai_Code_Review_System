import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import ReviewFinding, ReviewRun


async def get_review_result(
    session: AsyncSession,
    review_run_id: uuid.UUID,
) -> tuple[ReviewRun, list[ReviewFinding]] | None:
    review_run = await session.get(ReviewRun, review_run_id)
    if review_run is None:
        return None
    findings = list(
        (
            await session.execute(
                select(ReviewFinding)
                .where(ReviewFinding.review_run_id == review_run_id)
                .order_by(ReviewFinding.file_path, ReviewFinding.start_line)
            )
        ).scalars()
    )
    return review_run, findings
