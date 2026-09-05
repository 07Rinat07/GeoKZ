from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DepthReference, VerificationStatus, enum_type


class WellTrajectoryPoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "well_trajectory_points"
    __table_args__ = (
        UniqueConstraint("well_id", "station_index", name="uq_well_trajectory_station"),
        CheckConstraint("station_index >= 0", name="ck_well_trajectory_station_index"),
        CheckConstraint("measured_depth_m >= 0", name="ck_well_trajectory_md"),
        CheckConstraint(
            "inclination_deg IS NULL OR (inclination_deg >= 0 AND inclination_deg <= 180)",
            name="ck_well_trajectory_inclination",
        ),
        CheckConstraint(
            "azimuth_deg IS NULL OR (azimuth_deg >= 0 AND azimuth_deg < 360)",
            name="ck_well_trajectory_azimuth",
        ),
    )

    well_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wells.id", ondelete="CASCADE"),
        index=True,
    )
    station_index: Mapped[int] = mapped_column(Integer, nullable=False)
    measured_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    true_vertical_depth_m: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    tvdss_m: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    inclination_deg: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    azimuth_deg: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    location: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False)
    )
    survey_method: Mapped[str | None] = mapped_column(String(200))
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "well_trajectory_verification_status"),
        default=VerificationStatus.DRAFT,
        server_default=VerificationStatus.DRAFT.value,
        nullable=False,
    )


class WellLogRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "well_log_runs"
    __table_args__ = (
        CheckConstraint("top_depth_m >= 0", name="ck_well_log_runs_top_depth"),
        CheckConstraint("base_depth_m >= top_depth_m", name="ck_well_log_runs_depth_order"),
    )

    external_id: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    well_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wells.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    acquisition_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_number: Mapped[str | None] = mapped_column(String(100))
    top_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    base_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    depth_reference: Mapped[DepthReference] = mapped_column(
        enum_type(DepthReference, "well_log_depth_reference"),
        default=DepthReference.MD,
        server_default=DepthReference.MD.value,
        nullable=False,
    )
    acquisition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service_company: Mapped[str | None] = mapped_column(String(500))
    tool_name: Mapped[str | None] = mapped_column(String(500))
    file_format: Mapped[str | None] = mapped_column(String(100))
    storage_path: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
    )
    metadata_payload: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "well_log_run_verification_status"),
        default=VerificationStatus.DRAFT,
        server_default=VerificationStatus.DRAFT.value,
        nullable=False,
    )

    curves: Mapped[list["WellLogCurve"]] = relationship(
        back_populates="log_run",
        cascade="all, delete-orphan",
    )


class WellLogCurve(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "well_log_curves"
    __table_args__ = (
        UniqueConstraint("log_run_id", "mnemonic_original", name="uq_well_log_curve_mnemonic"),
        CheckConstraint("sample_count IS NULL OR sample_count >= 0", name="ck_log_curve_sample_count"),
    )

    log_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("well_log_runs.id", ondelete="CASCADE"),
        index=True,
    )
    mnemonic_original: Mapped[str] = mapped_column(String(200), nullable=False)
    property_kind: Mapped[str | None] = mapped_column(String(300), index=True)
    property_kind_code: Mapped[str | None] = mapped_column(String(160), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    unit_original: Mapped[str | None] = mapped_column(String(100))
    canonical_unit: Mapped[str | None] = mapped_column(String(100))
    unit_code: Mapped[str | None] = mapped_column(String(160), index=True)
    sample_count: Mapped[int | None] = mapped_column(Integer)
    min_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    max_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    storage_path: Mapped[str | None] = mapped_column(Text)
    metadata_payload: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    log_run: Mapped[WellLogRun] = relationship(back_populates="curves")


class WellTest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "well_tests"
    __table_args__ = (
        CheckConstraint("top_depth_m >= 0", name="ck_well_tests_top_depth"),
        CheckConstraint("base_depth_m >= top_depth_m", name="ck_well_tests_depth_order"),
        CheckConstraint("pressure_mpa IS NULL OR pressure_mpa >= 0", name="ck_well_tests_pressure"),
    )

    external_id: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    well_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wells.id", ondelete="CASCADE"),
        index=True,
    )
    test_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    test_date: Mapped[date | None] = mapped_column(Date)
    top_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    base_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    depth_reference: Mapped[DepthReference] = mapped_column(
        enum_type(DepthReference, "well_test_depth_reference"),
        default=DepthReference.MD,
        server_default=DepthReference.MD.value,
        nullable=False,
    )
    stratigraphic_unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="SET NULL"),
        index=True,
    )
    pressure_mpa: Mapped[Decimal | None] = mapped_column(Numeric(12, 5))
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    oil_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 5))
    oil_rate_unit: Mapped[str | None] = mapped_column(String(100))
    oil_rate_unit_code: Mapped[str | None] = mapped_column(String(160))
    gas_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 5))
    gas_rate_unit: Mapped[str | None] = mapped_column(String(100))
    gas_rate_unit_code: Mapped[str | None] = mapped_column(String(160))
    water_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 5))
    water_rate_unit: Mapped[str | None] = mapped_column(String(100))
    water_rate_unit_code: Mapped[str | None] = mapped_column(String(160))
    result_text: Mapped[str | None] = mapped_column(Text)
    interpretation_text: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "well_test_verification_status"),
        default=VerificationStatus.DRAFT,
        server_default=VerificationStatus.DRAFT.value,
        nullable=False,
    )


class CoreRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_runs"
    __table_args__ = (
        CheckConstraint("top_depth_m >= 0", name="ck_core_runs_top_depth"),
        CheckConstraint("base_depth_m >= top_depth_m", name="ck_core_runs_depth_order"),
        CheckConstraint(
            "recovery_percent IS NULL OR (recovery_percent >= 0 AND recovery_percent <= 100)",
            name="ck_core_runs_recovery",
        ),
    )

    external_id: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    well_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wells.id", ondelete="CASCADE"),
        index=True,
    )
    top_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    base_depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    depth_reference: Mapped[DepthReference] = mapped_column(
        enum_type(DepthReference, "core_run_depth_reference"),
        default=DepthReference.MD,
        server_default=DepthReference.MD.value,
        nullable=False,
    )
    recovery_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    description: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )

    samples: Mapped[list["CoreSample"]] = relationship(
        back_populates="core_run",
        cascade="all, delete-orphan",
    )


class CoreSample(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "core_samples"
    __table_args__ = (
        CheckConstraint("depth_m >= 0", name="ck_core_samples_depth"),
        CheckConstraint(
            "porosity_percent IS NULL OR (porosity_percent >= 0 AND porosity_percent <= 100)",
            name="ck_core_samples_porosity",
        ),
        CheckConstraint(
            "permeability_md IS NULL OR permeability_md >= 0",
            name="ck_core_samples_permeability",
        ),
    )

    core_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core_runs.id", ondelete="CASCADE"),
        index=True,
    )
    sample_code: Mapped[str | None] = mapped_column(String(200), index=True)
    depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    sample_type: Mapped[str | None] = mapped_column(String(100), index=True)
    lithologies: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    lithology_codes: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    porosity_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    permeability_md: Mapped[Decimal | None] = mapped_column(Numeric(16, 5))
    grain_density_g_cm3: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    measurements: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )

    core_run: Mapped[CoreRun] = relationship(back_populates="samples")


class SeismicSurvey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seismic_surveys"

    external_id: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    survey_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    acquisition_start: Mapped[date | None] = mapped_column(Date)
    acquisition_end: Mapped[date | None] = mapped_column(Date)
    operator: Mapped[str | None] = mapped_column(String(500))
    contractor: Mapped[str | None] = mapped_column(String(500))
    coordinate_system_original: Mapped[str | None] = mapped_column(String(300))
    coverage: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False)
    )
    acquisition_parameters: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    processing_history: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "seismic_survey_verification_status"),
        default=VerificationStatus.DRAFT,
        server_default=VerificationStatus.DRAFT.value,
        nullable=False,
    )

    lines: Mapped[list["SeismicLine"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
    )
    volumes: Mapped[list["SeismicVolume"]] = relationship(
        back_populates="survey",
        cascade="all, delete-orphan",
    )


class SeismicLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seismic_lines"
    __table_args__ = (
        UniqueConstraint("survey_id", "name", name="uq_seismic_lines_name"),
    )

    survey_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("seismic_surveys.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    geometry: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False)
    )
    sample_interval_ms: Mapped[Decimal | None] = mapped_column(Numeric(10, 5))
    storage_path: Mapped[str | None] = mapped_column(Text)
    file_format: Mapped[str | None] = mapped_column(String(100))
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
    )

    survey: Mapped[SeismicSurvey] = relationship(back_populates="lines")


class SeismicVolume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seismic_volumes"
    __table_args__ = (
        UniqueConstraint("survey_id", "name", name="uq_seismic_volumes_name"),
    )

    survey_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("seismic_surveys.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    footprint: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False)
    )
    inline_start: Mapped[int | None] = mapped_column(Integer)
    inline_end: Mapped[int | None] = mapped_column(Integer)
    crossline_start: Mapped[int | None] = mapped_column(Integer)
    crossline_end: Mapped[int | None] = mapped_column(Integer)
    sample_interval_ms: Mapped[Decimal | None] = mapped_column(Numeric(10, 5))
    storage_path: Mapped[str | None] = mapped_column(Text)
    file_format: Mapped[str | None] = mapped_column(String(100))
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
    )

    survey: Mapped[SeismicSurvey] = relationship(back_populates="volumes")
