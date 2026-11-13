from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ComponentHealthResponse(BaseModel):
    name: Literal["postgres", "redis"]
    status: Literal["ok", "error"]
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    components: list[ComponentHealthResponse]
