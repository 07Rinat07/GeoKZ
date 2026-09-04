"""Add persistent organization CRS definitions.

Revision ID: 20260904_0005
Revises: 20260904_0004
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260904_0005"
down_revision: str | None = "20260904_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "organization_crs_definitions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("name_ru", sa.String(300), nullable=False),
        sa.Column("name_kk", sa.String(300), nullable=False),
        sa.Column("name_en", sa.String(300), nullable=False),
        sa.Column("definition_kind", sa.String(16), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("canonical_wkt", sa.Text(), nullable=False),
        sa.Column("authority_name", sa.String(50)),
        sa.Column("authority_code", sa.String(100)),
        sa.Column("default_axis_order", sa.String(64), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "is_confirmed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("confirmed_by", sa.String(200)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("confirmation_note", sa.Text()),
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
            "definition_kind IN ('EPSG', 'WKT', 'PROJ')",
            name="ck_organization_crs_definition_kind",
        ),
        sa.CheckConstraint(
            "default_axis_order IN "
            "('x_easting_y_northing', 'x_northing_y_easting')",
            name="ck_organization_crs_axis_order",
        ),
        sa.CheckConstraint(
            "("
            "is_confirmed = false AND confirmed_by IS NULL AND confirmed_at IS NULL"
            ") OR ("
            "is_confirmed = true AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL"
            ")",
            name="ck_organization_crs_confirmation",
        ),
    )
    op.create_index(
        "ix_organization_crs_definitions_code",
        "organization_crs_definitions",
        ["code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_organization_crs_definitions_code",
        table_name="organization_crs_definitions",
    )
    op.drop_table("organization_crs_definitions")
