from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationCrsDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organization_crs_definitions"
    __table_args__ = (
        CheckConstraint(
            "definition_kind IN ('EPSG', 'WKT', 'PROJ')",
            name="ck_organization_crs_definition_kind",
        ),
        CheckConstraint(
            "default_axis_order IN "
            "('x_easting_y_northing', 'x_northing_y_easting')",
            name="ck_organization_crs_axis_order",
        ),
        CheckConstraint(
            "("
            "is_confirmed = false AND confirmed_by IS NULL AND confirmed_at IS NULL"
            ") OR ("
            "is_confirmed = true AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL"
            ")",
            name="ck_organization_crs_confirmation",
        ),
    )

    code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(300), nullable=False)
    name_kk: Mapped[str] = mapped_column(String(300), nullable=False)
    name_en: Mapped[str] = mapped_column(String(300), nullable=False)

    definition_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    authority_name: Mapped[str | None] = mapped_column(String(50))
    authority_code: Mapped[str | None] = mapped_column(String(100))
    default_axis_order: Mapped[str] = mapped_column(String(64), nullable=False)

    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    is_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    confirmed_by: Mapped[str | None] = mapped_column(String(200))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmation_note: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
