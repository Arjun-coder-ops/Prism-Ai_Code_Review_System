import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.integrations.github_webhook import verify_github_webhook_signature
from app.services.webhook_deliveries import record_webhook_delivery

router = APIRouter(prefix="/api/v1/github", tags=["github"])

_MAX_WEBHOOK_BYTES = 1_000_000
_SUPPORTED_EVENTS = {
    "installation",
    "installation_repositories",
    "ping",
    "pull_request",
}


@router.post("/webhooks", status_code=status.HTTP_202_ACCEPTED)
async def receive_github_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    x_github_delivery: Annotated[str | None, Header()] = None,
    x_github_event: Annotated[str | None, Header()] = None,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Authenticate a GitHub event before any future event-specific handling."""
    secret = get_settings().github_webhook_secret
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="webhook integration is not configured",
        )

    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isdigit():
        if int(content_length) > _MAX_WEBHOOK_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    payload = await request.body()
    if len(payload) > _MAX_WEBHOOK_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    if not verify_github_webhook_signature(
        payload=payload,
        signature=x_hub_signature_256,
        secret=secret.get_secret_value(),
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        decoded_payload = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from exc
    if not isinstance(decoded_payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if x_github_event not in _SUPPORTED_EVENTS:
        return {"status": "ignored"}
    try:
        delivery_id = uuid.UUID(x_github_delivery or "")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST) from exc
    action = decoded_payload.get("action")
    if action is not None and not isinstance(action, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    recorded = await record_webhook_delivery(
        session,
        delivery_id=delivery_id,
        event_name=x_github_event,
        action=action,
        payload=payload,
    )
    if not recorded:
        return {"status": "duplicate"}
    return {"status": "accepted"}
