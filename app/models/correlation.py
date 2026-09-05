from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DepthReference, VerificationStatus, enum_type


class WellMarker(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Стратиграфический/геофизический репер, используемый для корреляции разрезов."""

    __tablename__ = "well_markers"
    __table_args__ = (
        CheckConstraint("depth_m >= 0", name="ck_well_markers_depth"),
        CheckConstraint(
            "confidence_percent IS NULL OR (confidence_percent >= 0 AND confidence_percent <= 100)",
            name="ck_well_markers_confidence",
        ),
    )

    well_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wells.id", ondelete="CASCADE"),
        index=True,
    )
    marker_code: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    marker_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    marker_type_code: Mapped[str | None] = mapped_column(String(160), index=True)
    name_ru: Mapped[str | None] = mapped_column(String(500))
    name_kk: Mapped[str | None] = mapped_column(String(500))
    name_en: Mapped[str | None] = mapped_column(String(500))
    depth_m: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    depth_reference: Mapped[DepthReference] = mapped_column(
        enum_type(DepthReference, "well_marker_depth_reference"),
        default=DepthReference.TVDSS,
        server_default=DepthReference.TVDSS.value,
        nullable=False,
    )
    measured_depth_m: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    true_vertical_depth_m: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    tvdss_m: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    stratigraphic_unit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="SET NULL"),
        index=True,
    )
    interpretation_method: Mapped[str | None] = mapped_column(String(300))
    confidence_percent: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    notes: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        index=True,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "well_marker_verification_status"),
        default=VerificationStatus.DRAFT,
        server_default=VerificationStatus.DRAFT.value,
        nullable=False,
    )
