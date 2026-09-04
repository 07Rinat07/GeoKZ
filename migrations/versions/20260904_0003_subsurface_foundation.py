"""Add well trajectory, well-log, test, core and seismic tables.

Revision ID: 20260904_0003
Revises: 20260904_0002
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260904_0003"
down_revision: str | None = "20260904_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


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


def verification_enum(name: str) -> sa.Enum:
    return enum(
        "DRAFT",
        "REVIEWED",
        "VERIFIED",
        "CONFLICT",
        "REJECTED",
        "OBSOLETE",
        name=name,
    )


def depth_reference_enum(name: str) -> sa.Enum:
    return enum("MD", "TVD", "TVDSS", "UNKNOWN", name=name)


def upgrade() -> None:
    op.create_table(
        "well_trajectory_points",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("well_id", UUID, sa.ForeignKey("wells.id", ondelete="CASCADE"), nullable=False),
        sa.Column("station_index", sa.Integer(), nullable=False),
        sa.Column("measured_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column("true_vertical_depth_m", sa.Numeric(12, 3)),
        sa.Column("tvdss_m", sa.Numeric(12, 3)),
        sa.Column("inclination_deg", sa.Numeric(8, 4)),
        sa.Column("azimuth_deg", sa.Numeric(8, 4)),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        ),
        sa.Column("survey_method", sa.String(200)),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column(
            "verification_status",
            verification_enum("well_trajectory_verification_status"),
            server_default="DRAFT",
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint("station_index >= 0", name="ck_well_trajectory_station_index"),
        sa.CheckConstraint("measured_depth_m >= 0", name="ck_well_trajectory_md"),
        sa.CheckConstraint(
            "inclination_deg IS NULL OR (inclination_deg >= 0 AND inclination_deg <= 180)",
            name="ck_well_trajectory_inclination",
        ),
        sa.CheckConstraint(
            "azimuth_deg IS NULL OR (azimuth_deg >= 0 AND azimuth_deg < 360)",
            name="ck_well_trajectory_azimuth",
        ),
        sa.UniqueConstraint("well_id", "station_index", name="uq_well_trajectory_station"),
    )
    op.create_index("ix_well_trajectory_points_well_id", "well_trajectory_points", ["well_id"])
    op.create_index("ix_well_trajectory_points_source_id", "well_trajectory_points", ["source_id"])
    op.create_index(
        "ix_well_trajectory_points_location",
        "well_trajectory_points",
        ["location"],
        postgresql_using="gist",
    )

    op.create_table(
        "well_log_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(240), nullable=False),
        sa.Column("well_id", UUID, sa.ForeignKey("wells.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("acquisition_type", sa.String(100), nullable=False),
        sa.Column("run_number", sa.String(100)),
        sa.Column("top_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column("base_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "depth_reference",
            depth_reference_enum("well_log_depth_reference"),
            server_default="MD",
            nullable=False,
        ),
        sa.Column("acquisition_at", sa.DateTime(timezone=True)),
        sa.Column("service_company", sa.String(500)),
        sa.Column("tool_name", sa.String(500)),
        sa.Column("file_format", sa.String(100)),
        sa.Column("storage_path", sa.Text()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "verification_status",
            verification_enum("well_log_run_verification_status"),
            server_default="DRAFT",
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint("top_depth_m >= 0", name="ck_well_log_runs_top_depth"),
        sa.CheckConstraint("base_depth_m >= top_depth_m", name="ck_well_log_runs_depth_order"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_well_log_runs_external_id", "well_log_runs", ["external_id"])
    op.create_index("ix_well_log_runs_well_id", "well_log_runs", ["well_id"])
    op.create_index("ix_well_log_runs_acquisition_type", "well_log_runs", ["acquisition_type"])
    op.create_index("ix_well_log_runs_sha256", "well_log_runs", ["sha256"])
    op.create_index("ix_well_log_runs_source_id", "well_log_runs", ["source_id"])

    op.create_table(
        "well_log_curves",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "log_run_id",
            UUID,
            sa.ForeignKey("well_log_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mnemonic_original", sa.String(200), nullable=False),
        sa.Column("property_kind", sa.String(300)),
        sa.Column("description", sa.Text()),
        sa.Column("unit_original", sa.String(100)),
        sa.Column("canonical_unit", sa.String(100)),
        sa.Column("sample_count", sa.Integer()),
        sa.Column("min_value", sa.Numeric(24, 8)),
        sa.Column("max_value", sa.Numeric(24, 8)),
        sa.Column("storage_path", sa.Text()),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
        sa.CheckConstraint("sample_count IS NULL OR sample_count >= 0", name="ck_log_curve_sample_count"),
        sa.UniqueConstraint("log_run_id", "mnemonic_original", name="uq_well_log_curve_mnemonic"),
    )
    op.create_index("ix_well_log_curves_log_run_id", "well_log_curves", ["log_run_id"])
    op.create_index("ix_well_log_curves_property_kind", "well_log_curves", ["property_kind"])

    op.create_table(
        "well_tests",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(240), nullable=False),
        sa.Column("well_id", UUID, sa.ForeignKey("wells.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_type", sa.String(100), nullable=False),
        sa.Column("test_date", sa.Date()),
        sa.Column("top_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column("base_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "depth_reference",
            depth_reference_enum("well_test_depth_reference"),
            server_default="MD",
            nullable=False,
        ),
        sa.Column(
            "stratigraphic_unit_id",
            UUID,
            sa.ForeignKey("geological_entities.id", ondelete="SET NULL"),
        ),
        sa.Column("pressure_mpa", sa.Numeric(12, 5)),
        sa.Column("temperature_c", sa.Numeric(10, 3)),
        sa.Column("oil_rate", sa.Numeric(20, 5)),
        sa.Column("oil_rate_unit", sa.String(100)),
        sa.Column("gas_rate", sa.Numeric(20, 5)),
        sa.Column("gas_rate_unit", sa.String(100)),
        sa.Column("water_rate", sa.Numeric(20, 5)),
        sa.Column("water_rate_unit", sa.String(100)),
        sa.Column("result_text", sa.Text()),
        sa.Column("interpretation_text", sa.Text()),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column(
            "verification_status",
            verification_enum("well_test_verification_status"),
            server_default="DRAFT",
            nullable=False,
        ),
        *timestamps(),
        sa.CheckConstraint("top_depth_m >= 0", name="ck_well_tests_top_depth"),
        sa.CheckConstraint("base_depth_m >= top_depth_m", name="ck_well_tests_depth_order"),
        sa.CheckConstraint("pressure_mpa IS NULL OR pressure_mpa >= 0", name="ck_well_tests_pressure"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_well_tests_external_id", "well_tests", ["external_id"])
    op.create_index("ix_well_tests_well_id", "well_tests", ["well_id"])
    op.create_index("ix_well_tests_test_type", "well_tests", ["test_type"])
    op.create_index("ix_well_tests_stratigraphic_unit_id", "well_tests", ["stratigraphic_unit_id"])
    op.create_index("ix_well_tests_source_id", "well_tests", ["source_id"])

    op.create_table(
        "core_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(240), nullable=False),
        sa.Column("well_id", UUID, sa.ForeignKey("wells.id", ondelete="CASCADE"), nullable=False),
        sa.Column("top_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column("base_depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "depth_reference",
            depth_reference_enum("core_run_depth_reference"),
            server_default="MD",
            nullable=False,
        ),
        sa.Column("recovery_percent", sa.Numeric(7, 3)),
        sa.Column("description", sa.Text()),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        *timestamps(),
        sa.CheckConstraint("top_depth_m >= 0", name="ck_core_runs_top_depth"),
        sa.CheckConstraint("base_depth_m >= top_depth_m", name="ck_core_runs_depth_order"),
        sa.CheckConstraint(
            "recovery_percent IS NULL OR (recovery_percent >= 0 AND recovery_percent <= 100)",
            name="ck_core_runs_recovery",
        ),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_core_runs_external_id", "core_runs", ["external_id"])
    op.create_index("ix_core_runs_well_id", "core_runs", ["well_id"])
    op.create_index("ix_core_runs_source_id", "core_runs", ["source_id"])

    op.create_table(
        "core_samples",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("core_run_id", UUID, sa.ForeignKey("core_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sample_code", sa.String(200)),
        sa.Column("depth_m", sa.Numeric(12, 3), nullable=False),
        sa.Column("sample_type", sa.String(100)),
        sa.Column("lithologies", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("porosity_percent", sa.Numeric(7, 3)),
        sa.Column("permeability_md", sa.Numeric(16, 5)),
        sa.Column("grain_density_g_cm3", sa.Numeric(8, 4)),
        sa.Column("measurements", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        *timestamps(),
        sa.CheckConstraint("depth_m >= 0", name="ck_core_samples_depth"),
        sa.CheckConstraint(
            "porosity_percent IS NULL OR (porosity_percent >= 0 AND porosity_percent <= 100)",
            name="ck_core_samples_porosity",
        ),
        sa.CheckConstraint(
            "permeability_md IS NULL OR permeability_md >= 0",
            name="ck_core_samples_permeability",
        ),
    )
    op.create_index("ix_core_samples_core_run_id", "core_samples", ["core_run_id"])
    op.create_index("ix_core_samples_sample_code", "core_samples", ["sample_code"])
    op.create_index("ix_core_samples_sample_type", "core_samples", ["sample_type"])
    op.create_index("ix_core_samples_source_id", "core_samples", ["source_id"])

    op.create_table(
        "seismic_surveys",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(240), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("survey_type", sa.String(50), nullable=False),
        sa.Column("acquisition_start", sa.Date()),
        sa.Column("acquisition_end", sa.Date()),
        sa.Column("operator", sa.String(500)),
        sa.Column("contractor", sa.String(500)),
        sa.Column("coordinate_system_original", sa.String(300)),
        sa.Column(
            "coverage",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
        ),
        sa.Column("acquisition_parameters", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("processing_history", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column(
            "verification_status",
            verification_enum("seismic_survey_verification_status"),
            server_default="DRAFT",
            nullable=False,
        ),
        *timestamps(),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_seismic_surveys_external_id", "seismic_surveys", ["external_id"])
    op.create_index("ix_seismic_surveys_name", "seismic_surveys", ["name"])
    op.create_index("ix_seismic_surveys_survey_type", "seismic_surveys", ["survey_type"])
    op.create_index("ix_seismic_surveys_source_id", "seismic_surveys", ["source_id"])
    op.create_index(
        "ix_seismic_surveys_coverage",
        "seismic_surveys",
        ["coverage"],
        postgresql_using="gist",
    )

    op.create_table(
        "seismic_lines",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "survey_id",
            UUID,
            sa.ForeignKey("seismic_surveys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False),
        ),
        sa.Column("sample_interval_ms", sa.Numeric(10, 5)),
        sa.Column("storage_path", sa.Text()),
        sa.Column("file_format", sa.String(100)),
        sa.Column("sha256", sa.String(64)),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        *timestamps(),
        sa.UniqueConstraint("survey_id", "name", name="uq_seismic_lines_name"),
    )
    op.create_index("ix_seismic_lines_survey_id", "seismic_lines", ["survey_id"])
    op.create_index("ix_seismic_lines_name", "seismic_lines", ["name"])
    op.create_index("ix_seismic_lines_sha256", "seismic_lines", ["sha256"])
    op.create_index(
        "ix_seismic_lines_geometry",
        "seismic_lines",
        ["geometry"],
        postgresql_using="gist",
    )

    op.create_table(
        "seismic_volumes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "survey_id",
            UUID,
            sa.ForeignKey("seismic_surveys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column(
            "footprint",
            geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
        ),
        sa.Column("inline_start", sa.Integer()),
        sa.Column("inline_end", sa.Integer()),
        sa.Column("crossline_start", sa.Integer()),
        sa.Column("crossline_end", sa.Integer()),
        sa.Column("sample_interval_ms", sa.Numeric(10, 5)),
        sa.Column("storage_path", sa.Text()),
        sa.Column("file_format", sa.String(100)),
        sa.Column("sha256", sa.String(64)),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        *timestamps(),
        sa.UniqueConstraint("survey_id", "name", name="uq_seismic_volumes_name"),
    )
    op.create_index("ix_seismic_volumes_survey_id", "seismic_volumes", ["survey_id"])
    op.create_index("ix_seismic_volumes_name", "seismic_volumes", ["name"])
    op.create_index("ix_seismic_volumes_sha256", "seismic_volumes", ["sha256"])
    op.create_index(
        "ix_seismic_volumes_footprint",
        "seismic_volumes",
        ["footprint"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_table("seismic_volumes")
    op.drop_table("seismic_lines")
    op.drop_table("seismic_surveys")
    op.drop_table("core_samples")
    op.drop_table("core_runs")
    op.drop_table("well_tests")
    op.drop_table("well_log_curves")
    op.drop_table("well_log_runs")
    op.drop_table("well_trajectory_points")
