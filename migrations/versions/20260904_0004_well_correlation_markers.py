"""Add well correlation markers.

Revision ID: 20260904_0004
Revises: 20260904_0003
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260904_0004"
down_revision: str | None = "20260904_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def enum(*values: str, name: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "well_markers",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "well_id",
            UUID,
            sa.ForeignKey("wells.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("marker_code", sa.String(200), nullable=False),
        sa.Column("marker_type", sa.String(100), nullable=False),
        sa.Column("name_ru", sa.String(500)),
        sa.Column("name_kk", sa.String(500)),
        sa.Column("name_en", sa.String(500)),
        sa.Column("depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "depth_reference",
            enum("MD", "TVD", "TVDSS", "UNKNOWN", name="well_marker_depth_reference"),
            server_default="TVDSS",
            nullable=False,
        ),
        sa.Column("measured_depth_m", sa.Numeric(12, 3)),
        sa.Column("true_vertical_depth_m", sa.Numeric(12, 3)),
        sa.Column("tvdss_m", sa.Numeric(12, 3)),
        sa.Column(
            "stratigraphic_unit_id",
            UUID,
            sa.ForeignKey("geological_entities.id", ondelete="SET NULL"),
        ),
        sa.Column("interpretation_method", sa.String(300)),
        sa.Column("confidence_percent", sa.Numeric(6, 3)),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("sources.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "verification_status",
            enum(
                "DRAFT",
                "REVIEWED",
                "VERIFIED",
                "CONFLICT",
                "REJECTED",
                "OBSOLETE",
                name="well_marker_verification_status",
            ),
            server_default="DRAFT",
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint("depth_m >= 0", name="ck_well_markers_depth"),
        sa.CheckConstraint(
            "confidence_percent IS NULL OR (confidence_percent >= 0 AND confidence_percent <= 100)",
            name="ck_well_markers_confidence",
        ),
    )
    op.create_index("ix_well_markers_well_id", "well_markers", ["well_id"])
    op.create_index("ix_well_markers_marker_code", "well_markers", ["marker_code"])
    op.create_index("ix_well_markers_marker_type", "well_markers", ["marker_type"])
    op.create_index(
        "ix_well_markers_stratigraphic_unit_id",
        "well_markers",
        ["stratigraphic_unit_id"],
    )
    op.create_index("ix_well_markers_source_id", "well_markers", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_well_markers_source_id", table_name="well_markers")
    op.drop_index("ix_well_markers_stratigraphic_unit_id", table_name="well_markers")
    op.drop_index("ix_well_markers_marker_type", table_name="well_markers")
    op.drop_index("ix_well_markers_marker_code", table_name="well_markers")
    op.drop_index("ix_well_markers_well_id", table_name="well_markers")
    op.drop_table("well_markers")
