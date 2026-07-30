from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AccessLevel,
    ReliabilityLevel,
    SourceDocumentType,
    enum_type,
)


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint(
            "publication_year IS NULL OR publication_year BETWEEN 1500 AND 2100",
            name="ck_sources_publication_year",
        ),
        CheckConstraint(
            "survey_year_start IS NULL OR survey_year_start BETWEEN 1500 AND 2100",
            name="ck_sources_survey_year_start",
        ),
        CheckConstraint(
            "survey_year_end IS NULL OR survey_year_end BETWEEN 1500 AND 2100",
            name="ck_sources_survey_year_end",
        ),
    )

    external_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    organization: Mapped[str | None] = mapped_column(String(500))
    publication_year: Mapped[int | None] = mapped_column(SmallInteger)
    survey_year_start: Mapped[int | None] = mapped_column(SmallInteger)
    survey_year_end: Mapped[int | None] = mapped_column(SmallInteger)
    document_type: Mapped[SourceDocumentType] = mapped_column(
        enum_type(SourceDocumentType, "source_document_type"),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(16), default="ru", nullable=False)
    territories: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    objects: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    inventory_number: Mapped[str | None] = mapped_column(String(200))
    doi: Mapped[str | None] = mapped_column(String(300), index=True)
    url: Mapped[str | None] = mapped_column(Text)
    access_date: Mapped[date | None]
    access_level: Mapped[AccessLevel] = mapped_column(
        enum_type(AccessLevel, "source_access_level"),
        default=AccessLevel.LOCAL,
        nullable=False,
    )
    page_count: Mapped[int | None]
    map_scale: Mapped[str | None] = mapped_column(String(100))
    coordinate_system: Mapped[str | None] = mapped_column(String(300))
    license: Mapped[str | None] = mapped_column(String(500))
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    reliability_level: Mapped[ReliabilityLevel] = mapped_column(
        enum_type(ReliabilityLevel, "source_reliability_level"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
