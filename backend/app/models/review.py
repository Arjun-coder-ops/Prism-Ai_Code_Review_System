import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampedModel:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampedModel, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    github_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)


class GitHubInstallation(TimestampedModel, Base):
    __tablename__ = "github_installations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    github_installation_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    owner_github_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    permission_metadata: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    installation_status: Mapped[str] = mapped_column(String(32), nullable=False)


class Repository(TimestampedModel, Base):
    __tablename__ = "repositories"
    __table_args__ = (Index("ix_repositories_installation_id", "installation_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    github_repository_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    installation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("github_installations.id"), nullable=True
    )
    owner: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False)
    default_branch: Mapped[str] = mapped_column(Text, nullable=False)


class PullRequest(TimestampedModel, Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        Index(
            "uq_pull_requests_repository_number",
            "repository_id",
            "github_pr_number",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id"), nullable=False
    )
    github_pr_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    base_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    current_head_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)


class ReviewRun(TimestampedModel, Base):
    __tablename__ = "review_runs"
    __table_args__ = (
        Index("ix_review_runs_pull_request_id", "pull_request_id"),
        Index(
            "uq_review_runs_revision_policy",
            "pull_request_id",
            "reviewed_head_sha",
            "review_policy_version",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pull_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pull_requests.id"), nullable=False
    )
    reviewed_head_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    review_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_identifier: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    token_usage: Mapped[int | None] = mapped_column(BigInteger)
    estimated_cost: Mapped[str | None] = mapped_column(String(32))


class ReviewFinding(Base):
    __tablename__ = "review_findings"
    __table_args__ = (Index("ix_review_findings_review_run_id", "review_run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    review_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("review_runs.id"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int] = mapped_column(nullable=False)
    end_line: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GitHubWebhookDelivery(Base):
    """Minimal, deduplicated audit record for a verified webhook delivery."""

    __tablename__ = "github_webhook_deliveries"
    __table_args__ = (Index("ix_webhook_deliveries_received_at", "received_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    github_delivery_id: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False)
    event_name: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str | None] = mapped_column(String(64))
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
