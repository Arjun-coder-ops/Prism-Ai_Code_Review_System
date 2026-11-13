import asyncio
import os
import uuid
from collections.abc import Coroutine
from typing import Any

from celery import Task
from celery.signals import worker_process_shutdown

from app.db.session import engine
from app.services.review_processor import RetryableReviewProcessingError
from app.services.review_processor import process_review_run as process_review_run_async
from app.workers.celery_app import celery_app

_worker_loop: asyncio.AbstractEventLoop | None = None
_worker_loop_pid: int | None = None


def _run_in_worker_loop(coroutine: Coroutine[Any, Any, str]) -> str:
    """Run async database work on one event loop per forked worker process.

    ``asyncio.run`` creates and closes a loop for every task. Asyncpg pools are
    tied to the loop that created their connections, so repeated task delivery
    must instead reuse the child process's loop.
    """
    global _worker_loop, _worker_loop_pid
    process_id = os.getpid()
    if (
        _worker_loop is None
        or _worker_loop.is_closed()
        or _worker_loop_pid != process_id
    ):
        _worker_loop = asyncio.new_event_loop()
        _worker_loop_pid = process_id
    asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


@worker_process_shutdown.connect
def close_worker_event_loop(**_: object) -> None:
    """Release async database connections as a prefork child exits."""
    global _worker_loop, _worker_loop_pid
    if _worker_loop is not None and not _worker_loop.is_closed():
        _worker_loop.run_until_complete(engine.dispose())
        _worker_loop.close()
    _worker_loop = None
    _worker_loop_pid = None


@celery_app.task(
    bind=True,
    name="prism.process_review_run",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(),
    retry_backoff=True,
    retry_jitter=True,
)
def process_review_run(self: Task, review_run_id: str) -> str:
    """Run a durable review by ID, with bounded retries for upstream failures."""
    try:
        parsed_id = uuid.UUID(review_run_id)
    except ValueError:
        return "invalid_review_run_id"
    try:
        return _run_in_worker_loop(process_review_run_async(parsed_id))
    except RetryableReviewProcessingError as exc:
        if self.request.retries >= self.max_retries:
            return "failed"
        raise self.retry(exc=exc) from exc
