from typing import Literal

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    pull_request_url: str = Field(min_length=1, max_length=512)


class AcceptedReviewResponse(BaseModel):
    id: str
    status: Literal["queued"]
    head_sha: str
