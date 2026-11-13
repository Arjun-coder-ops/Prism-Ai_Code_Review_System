"""Create initial PRISM review persistence schema.

Revision ID: 20261112_0001
Revises:
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261112_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("github_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_user_id"),
    )
    op.create_table(
        "github_installations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("github_installation_id", sa.BigInteger(), nullable=False),
        sa.Column("owner_github_id", sa.BigInteger(), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column(
            "permission_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("installation_status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_installation_id"),
    )
    op.create_table(
        "repositories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("github_repository_id", sa.BigInteger(), nullable=False),
        sa.Column("installation_id", sa.Uuid(), nullable=True),
        sa.Column("owner", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("default_branch", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["installation_id"], ["github_installations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_name"),
        sa.UniqueConstraint("github_repository_id"),
    )
    op.create_index(
        "ix_repositories_installation_id", "repositories", ["installation_id"]
    )
    op.create_table(
        "pull_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("github_pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("base_sha", sa.String(length=64), nullable=False),
        sa.Column("current_head_sha", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_pull_requests_repository_number",
        "pull_requests",
        ["repository_id", "github_pr_number"],
        unique=True,
    )
    op.create_table(
        "review_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pull_request_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_head_sha", sa.String(length=64), nullable=False),
        sa.Column("review_policy_version", sa.String(length=64), nullable=False),
        sa.Column("model_identifier", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("token_usage", sa.BigInteger(), nullable=True),
        sa.Column("estimated_cost", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_runs_pull_request_id", "review_runs", ["pull_request_id"]
    )
    op.create_index(
        "uq_review_runs_revision_policy",
        "review_runs",
        ["pull_request_id", "reviewed_head_sha", "review_policy_version"],
        unique=True,
    )
    op.create_table(
        "review_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("review_run_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["review_run_id"], ["review_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_findings_review_run_id", "review_findings", ["review_run_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_review_findings_review_run_id", table_name="review_findings")
    op.drop_table("review_findings")
    op.drop_index("uq_review_runs_revision_policy", table_name="review_runs")
    op.drop_index("ix_review_runs_pull_request_id", table_name="review_runs")
    op.drop_table("review_runs")
    op.drop_index("uq_pull_requests_repository_number", table_name="pull_requests")
    op.drop_table("pull_requests")
    op.drop_index("ix_repositories_installation_id", table_name="repositories")
    op.drop_table("repositories")
    op.drop_table("github_installations")
    op.drop_table("users")
