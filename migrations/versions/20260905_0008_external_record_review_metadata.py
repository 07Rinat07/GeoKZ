"""Add generic reviewer metadata to external records.

Revision ID: 20260905_0008
Revises: 20260905_0007
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260905_0008"
down_revision: str | None = "20260905_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "external_records",
        sa.Column("reviewed_by", sa.String(length=300), nullable=True),
    )
    op.add_column(
        "external_records",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "external_records",
        sa.Column("review_comment", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("external_records", "review_comment")
    op.drop_column("external_records", "reviewed_at")
    op.drop_column("external_records", "reviewed_by")
