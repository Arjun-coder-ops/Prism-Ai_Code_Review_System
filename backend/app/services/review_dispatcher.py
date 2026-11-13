from typing import Protocol

from app.workers.tasks import process_review_run


class ReviewDispatcher(Protocol):
    def enqueue(self, review_run_id: str) -> None: ...


class CeleryReviewDispatcher:
    """Publish only a primitive review ID to the durable Celery queue."""

    def enqueue(self, review_run_id: str) -> None:
        process_review_run.delay(review_run_id)
