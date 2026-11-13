from typing import Literal

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    pull_request_url: str = Field(min_length=1, max_length=512)


class AcceptedReviewResponse(BaseModel):
    id: str
    status: Literal["queued"]
    head_sha: str


class FindingResponse(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    category: str
    severity: str
    title: str
    explanation: str
    evidence: dict[str, object]
    verification_status: str


class ReviewStatusResponse(BaseModel):
    id: str
    status: str
    head_sha: str
    findings: list[FindingResponse]
