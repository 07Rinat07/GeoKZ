from datetime import date
from decimal import Decimal
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    CoordinateAccuracy,
    DepthReference,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
    WellType,
    enum_type,
)


class Well(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "wells"
    __table_args__ = (
        CheckConstraint("total_depth_m IS NULL OR total_depth_m >= 0", name="ck_wells_depth"),
    )

    external_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    aliases: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    object_entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="SET NULL"),
        index=True,
    )
    well_type: Mapped[WellType] = mapped_column(
        enum_type(WellType, "well_type"),
        nullable=False,
    )
    spud_date: Mapped[date | None] = mapped_column(Date)
    completion_date: Mapped[date | None] = mapped_column(Date)
    total_depth_m: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    location: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False)
    )
    coordinate_system_original: Mapped[str | None] = mapped_column(String(300))
    coordinate_accuracy: Mapped[CoordinateAccuracy] = mapped_column(
        enum_type(CoordinateAccuracy, "well_coordinate_accuracy"),
        default=CoordinateAccuracy.UNKNOWN,
        nullable=False,
    )
    operator: Mapped[str | None] = mapped_column(String(500))
    bottomhole_unit: Mapped[str | None] = mapped_column(String(300))
    core_available: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    logs_available: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    tests_available: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[str | None] = mapped_column(String(200))
    source_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "well_verification_status"),
        default=VerificationStatus.DRAFT,
        nullable=False,
    )

    intervals: Mapped[list["WellInterval"]] = relationship(
        back_populates="well",
        cascade="all, delete-orphan",
    )


class WellInterval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "well_intervals"
    __table_args__ = (
        CheckConstraint("top_depth_m >= 0", name="ck_intervals_top_depth"),
        CheckConstraint("base_depth_m >= top_depth_m", name="ck_intervals_depth_order"),
    )

    external_id: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    well_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wells.id", ondelete="CASCADE"),
        index=True,
    )
    top_depth_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    base_depth_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    depth_reference: Mapped[DepthReference] = mapped_column(
        enum_type(DepthReference, "interval_depth_reference"),
        default=DepthReference.UNKNOWN,
        nullable=False,
    )
    stratigraphic_unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="SET NULL"),
    )
    local_horizon: Mapped[str | None] = mapped_column(String(300), index=True)
    lithologies: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    porosity_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    permeability_md: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    net_pay_m: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fluid_type: Mapped[FluidType] = mapped_column(
        enum_type(FluidType, "interval_fluid_type"),
        default=FluidType.UNKNOWN,
        nullable=False,
    )
    hydrocarbon_status: Mapped[HydrocarbonStatus] = mapped_column(
        enum_type(HydrocarbonStatus, "interval_hydrocarbon_status"),
        default=HydrocarbonStatus.UNKNOWN,
        nullable=False,
    )
    test_result: Mapped[str | None] = mapped_column(Text)
    flow_rate: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    flow_rate_unit: Mapped[str | None] = mapped_column(String(100))
    pressure_mpa: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    source_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "interval_verification_status"),
        default=VerificationStatus.DRAFT,
        nullable=False,
    )

    well: Mapped[Well] = relationship(back_populates="intervals")
