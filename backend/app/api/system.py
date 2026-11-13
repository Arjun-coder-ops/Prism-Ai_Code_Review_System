from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_readiness_service
from app.schemas.system import (
    ComponentHealthResponse,
    HealthResponse,
    ReadinessResponse,
)
from app.services.readiness import ReadinessService

router = APIRouter(tags=["system"])

ReadinessDependency = Annotated[ReadinessService, Depends(get_readiness_service)]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report whether the process can handle HTTP requests."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
async def ready(
    response: Response,
    readiness_service: ReadinessDependency,
) -> ReadinessResponse:
    """Report whether configured infrastructure dependencies are reachable."""
    components = await readiness_service.check()
    is_ready = all(component.status == "ok" for component in components)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ok" if is_ready else "degraded",
        components=[
            ComponentHealthResponse(
                name=component.name,
                status=component.status,
                detail=component.detail,
            )
            for component in components
        ],
    )
