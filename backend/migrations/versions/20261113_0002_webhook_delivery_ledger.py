"""Add a minimal deduplicated GitHub webhook delivery ledger.

Revision ID: 20261113_0002
Revises: 20261112_0001
Create Date: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261113_0002"
down_revision: str | None = "20261112_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_webhook_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("github_delivery_id", sa.Uuid(), nullable=False),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=True),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_delivery_id"),
    )
    op.create_index(
        "ix_webhook_deliveries_received_at",
        "github_webhook_deliveries",
        ["received_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_webhook_deliveries_received_at",
        table_name="github_webhook_deliveries",
    )
    op.drop_table("github_webhook_deliveries")
