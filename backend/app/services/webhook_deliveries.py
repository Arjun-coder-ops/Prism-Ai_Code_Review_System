import hashlib
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import GitHubWebhookDelivery


async def record_webhook_delivery(
    session: AsyncSession,
    *,
    delivery_id: uuid.UUID,
    event_name: str,
    action: str | None,
    payload: bytes,
) -> bool:
    """Persist a verified delivery exactly once without retaining its body."""
    session.add(
        GitHubWebhookDelivery(
            github_delivery_id=delivery_id,
            event_name=event_name,
            action=action,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            processing_status="received",
        )
    )
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return False
    return True
