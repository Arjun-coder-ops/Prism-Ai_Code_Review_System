import uuid

from app.workers import tasks
from app.workers.celery_app import celery_app
from app.workers.tasks import process_review_run


def test_configures_safe_json_celery_review_queue() -> None:
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.task_default_queue == "prism.review"


def test_rejects_invalid_review_ids_without_dispatching_work() -> None:
    assert process_review_run.run("not-a-uuid") == "invalid_review_run_id"


def test_worker_reuses_one_event_loop_for_multiple_valid_tasks(monkeypatch) -> None:
    received: list[uuid.UUID] = []

    async def fake_processor(review_run_id: uuid.UUID) -> str:
        received.append(review_run_id)
        return "completed"

    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    monkeypatch.setattr(tasks, "process_review_run_async", fake_processor)
    try:
        assert process_review_run.run(str(first_id)) == "completed"
        first_loop = tasks._worker_loop
        assert process_review_run.run(str(second_id)) == "completed"
        assert tasks._worker_loop is first_loop
        assert received == [first_id, second_id]
    finally:
        tasks.close_worker_event_loop()
