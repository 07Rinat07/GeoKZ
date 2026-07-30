from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdministrativeRegion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "administrative_regions"

    external_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("administrative_regions.id", ondelete="SET NULL"),
        index=True,
    )
    level: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name_ru: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_kk: Mapped[str | None] = mapped_column(String(500))
    name_en: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    geometry: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False)
    )

    parent: Mapped["AdministrativeRegion | None"] = relationship(
        remote_side="AdministrativeRegion.id",
        back_populates="children",
    )
    children: Mapped[list["AdministrativeRegion"]] = relationship(back_populates="parent")
