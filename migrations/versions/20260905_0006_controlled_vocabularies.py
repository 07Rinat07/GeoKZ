"""Add controlled geological vocabulary registry.

Revision ID: 20260905_0006
Revises: 20260904_0005
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260905_0006"
down_revision: str | None = "20260904_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "controlled_vocabulary_terms",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("vocabulary", sa.String(64), nullable=False),
        sa.Column("code", sa.String(160), nullable=False),
        sa.Column("name_ru", sa.String(300), nullable=False),
        sa.Column("name_kk", sa.String(300), nullable=False),
        sa.Column("name_en", sa.String(300), nullable=False),
        sa.Column(
            "aliases",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("description", sa.Text()),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "vocabulary IN ('lithology', 'marker_type', 'property_kind', 'unit')",
            name="ck_controlled_vocabulary_code",
        ),
        sa.UniqueConstraint(
            "vocabulary",
            "code",
            name="uq_controlled_vocabulary_term_code",
        ),
    )
    op.create_index(
        "ix_controlled_vocabulary_terms_vocabulary",
        "controlled_vocabulary_terms",
        ["vocabulary"],
    )
    op.create_index(
        "ix_controlled_vocabulary_terms_code",
        "controlled_vocabulary_terms",
        ["code"],
    )
    op.create_index(
        "ix_controlled_vocabulary_terms_is_active",
        "controlled_vocabulary_terms",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_controlled_vocabulary_terms_is_active",
        table_name="controlled_vocabulary_terms",
    )
    op.drop_index(
        "ix_controlled_vocabulary_terms_code",
        table_name="controlled_vocabulary_terms",
    )
    op.drop_index(
        "ix_controlled_vocabulary_terms_vocabulary",
        table_name="controlled_vocabulary_terms",
    )
    op.drop_table("controlled_vocabulary_terms")
