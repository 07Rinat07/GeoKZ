"""Add Core Dataset update-channel rollback and provenance state.

Revision ID: 20260905_0011
Revises: 20260905_0010
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260905_0011"
down_revision: str | None = "20260905_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_dataset_version", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_schema_version", sa.Integer(), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_manifest_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_installed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_source_path", sa.Text(), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_file_checksums", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("previous_item_counts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("last_update_source_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("last_update_bundle_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "core_dataset_states",
        sa.Column("last_update_key_id", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    for column in (
        "last_update_key_id",
        "last_update_bundle_sha256",
        "last_update_source_url",
        "previous_item_counts",
        "previous_file_checksums",
        "previous_source_path",
        "previous_installed_at",
        "previous_manifest_sha256",
        "previous_schema_version",
        "previous_dataset_version",
    ):
        op.drop_column("core_dataset_states", column)
