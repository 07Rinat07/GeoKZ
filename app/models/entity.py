from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    EntityNameType,
    GeometryStatus,
    VerificationStatus,
    enum_type,
)

geological_entity_administrative_regions = Table(
    "geological_entity_administrative_regions",
    Base.metadata,
    Column(
        "entity_id",
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "administrative_region_id",
        PGUUID(as_uuid=True),
        ForeignKey("administrative_regions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("relation_type", String(64), nullable=False, server_default="located_in"),
)


class GeologicalEntity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "geological_entities"

    external_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    object_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="SET NULL"),
        index=True,
    )
    name_ru: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_kk: Mapped[str | None] = mapped_column(String(500))
    name_en: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    geological_context: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    geometry: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False)
    )
    geometry_status: Mapped[GeometryStatus] = mapped_column(
        enum_type(GeometryStatus, "entity_geometry_status"),
        default=GeometryStatus.UNKNOWN,
        nullable=False,
    )
    geometry_source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "entity_verification_status"),
        default=VerificationStatus.DRAFT,
        nullable=False,
    )

    parent: Mapped["GeologicalEntity | None"] = relationship(
        remote_side="GeologicalEntity.id",
        back_populates="children",
    )
    children: Mapped[list["GeologicalEntity"]] = relationship(back_populates="parent")
    names: Mapped[list["EntityName"]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan",
    )
    administrative_regions: Mapped[list["AdministrativeRegion"]] = relationship(
        secondary=geological_entity_administrative_regions,
    )


class EntityName(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "entity_names"
    __table_args__ = (
        UniqueConstraint("entity_id", "name", "language", name="uq_entity_names_value"),
    )

    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(16), default="ru", nullable=False)
    name_type: Mapped[EntityNameType] = mapped_column(
        enum_type(EntityNameType, "entity_name_type"),
        nullable=False,
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
    )
    is_preferred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    entity: Mapped[GeologicalEntity] = relationship(back_populates="names")
