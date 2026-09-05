"""Bind controlled vocabulary codes to subsurface domain records.

Revision ID: 20260905_0007
Revises: 20260905_0006
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260905_0007"
down_revision: str | None = "20260905_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "well_intervals",
        sa.Column(
            "lithology_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "well_intervals",
        sa.Column("flow_rate_unit_code", sa.String(160)),
    )
    op.create_index(
        "ix_well_intervals_flow_rate_unit_code",
        "well_intervals",
        ["flow_rate_unit_code"],
    )

    op.add_column(
        "well_markers",
        sa.Column("marker_type_code", sa.String(160)),
    )
    op.create_index(
        "ix_well_markers_marker_type_code",
        "well_markers",
        ["marker_type_code"],
    )

    op.add_column(
        "well_log_curves",
        sa.Column("property_kind_code", sa.String(160)),
    )
    op.add_column(
        "well_log_curves",
        sa.Column("unit_code", sa.String(160)),
    )
    op.create_index(
        "ix_well_log_curves_property_kind_code",
        "well_log_curves",
        ["property_kind_code"],
    )
    op.create_index(
        "ix_well_log_curves_unit_code",
        "well_log_curves",
        ["unit_code"],
    )

    op.add_column(
        "well_tests",
        sa.Column("oil_rate_unit_code", sa.String(160)),
    )
    op.add_column(
        "well_tests",
        sa.Column("gas_rate_unit_code", sa.String(160)),
    )
    op.add_column(
        "well_tests",
        sa.Column("water_rate_unit_code", sa.String(160)),
    )

    op.add_column(
        "core_samples",
        sa.Column(
            "lithology_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("core_samples", "lithology_codes")

    op.drop_column("well_tests", "water_rate_unit_code")
    op.drop_column("well_tests", "gas_rate_unit_code")
    op.drop_column("well_tests", "oil_rate_unit_code")

    op.drop_index(
        "ix_well_log_curves_unit_code",
        table_name="well_log_curves",
    )
    op.drop_index(
        "ix_well_log_curves_property_kind_code",
        table_name="well_log_curves",
    )
    op.drop_column("well_log_curves", "unit_code")
    op.drop_column("well_log_curves", "property_kind_code")

    op.drop_index(
        "ix_well_markers_marker_type_code",
        table_name="well_markers",
    )
    op.drop_column("well_markers", "marker_type_code")

    op.drop_index(
        "ix_well_intervals_flow_rate_unit_code",
        table_name="well_intervals",
    )
    op.drop_column("well_intervals", "flow_rate_unit_code")
    op.drop_column("well_intervals", "lithology_codes")
