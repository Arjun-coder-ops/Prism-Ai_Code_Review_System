from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("prism", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_default_queue="prism.review",
    task_soft_time_limit=240,
    task_time_limit=300,
    imports=("app.workers.tasks",),
)
