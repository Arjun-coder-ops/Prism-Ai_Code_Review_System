import hashlib
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.webhook_deliveries import record_webhook_delivery


@pytest.mark.anyio
async def test_records_only_a_delivery_digest_and_metadata() -> None:
    delivery_id = uuid.uuid4()
    payload = b'{"repository":{"private":true}}'

    class Session:
        added: object | None = None

        def add(self, value: object) -> None:
            self.added = value

        async def commit(self) -> None:
            return None

        async def rollback(self) -> None:
            return None

    session = Session()
    assert await record_webhook_delivery(
        session,  # type: ignore[arg-type]
        delivery_id=delivery_id,
        event_name="pull_request",
        action="opened",
        payload=payload,
    )
    assert session.added is not None
    assert session.added.payload_sha256 == hashlib.sha256(payload).hexdigest()
    assert not hasattr(session.added, "payload")


@pytest.mark.anyio
async def test_duplicate_delivery_rolls_back_without_failure() -> None:
    class Session:
        def add(self, _: object) -> None:
            return None

        async def commit(self) -> None:
            raise IntegrityError("duplicate", {}, RuntimeError("duplicate"))

        async def rollback(self) -> None:
            return None

    assert not await record_webhook_delivery(
        Session(),  # type: ignore[arg-type]
        delivery_id=uuid.uuid4(),
        event_name="ping",
        action=None,
        payload=b"{}",
    )
