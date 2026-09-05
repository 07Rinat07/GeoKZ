"""Add independently versioned GeoKZ Core Dataset state.

Revision ID: 20260905_0009
Revises: 20260905_0008
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260905_0009"
down_revision: str | None = "20260905_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "core_dataset_states",
        sa.Column("dataset_code", sa.String(length=120), nullable=False),
        sa.Column("dataset_version", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("manifest_sha256", sa.String(length=64), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column(
            "file_checksums",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "item_counts",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_code"),
    )
    op.create_index(
        op.f("ix_core_dataset_states_dataset_code"),
        "core_dataset_states",
        ["dataset_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_core_dataset_states_dataset_version"),
        "core_dataset_states",
        ["dataset_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_core_dataset_states_dataset_version"), table_name="core_dataset_states")
    op.drop_index(op.f("ix_core_dataset_states_dataset_code"), table_name="core_dataset_states")
    op.drop_table("core_dataset_states")
