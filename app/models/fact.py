from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ConfidenceLevel,
    EvidenceRole,
    ExtractionMethod,
    FactCategory,
    FactKind,
    VerificationStatus,
    enum_type,
)


class Fact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "facts"
    __table_args__ = (
        CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_facts_page_number"),
    )

    external_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    primary_source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        index=True,
    )
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="SET NULL"),
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    category: Mapped[FactCategory] = mapped_column(
        enum_type(FactCategory, "fact_category"),
        nullable=False,
        index=True,
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_statement: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    figure_number: Mapped[str | None] = mapped_column(String(100))
    table_number: Mapped[str | None] = mapped_column(String(100))
    section_title: Mapped[str | None] = mapped_column(String(1000))
    methods: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )
    fact_kind: Mapped[FactKind] = mapped_column(
        enum_type(FactKind, "fact_kind"),
        nullable=False,
    )
    valid_time_start: Mapped[int | None] = mapped_column(SmallInteger)
    valid_time_end: Mapped[int | None] = mapped_column(SmallInteger)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        enum_type(ConfidenceLevel, "fact_confidence"),
        default=ConfidenceLevel.UNKNOWN,
        nullable=False,
    )
    needs_human_review: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    review_reason: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "fact_verification_status"),
        default=VerificationStatus.DRAFT,
        nullable=False,
    )
    related_fact_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default="[]",
        nullable=False,
    )

    evidences: Mapped[list["FactEvidence"]] = relationship(
        back_populates="fact",
        cascade="all, delete-orphan",
    )


class FactEvidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fact_evidences"
    __table_args__ = (
        CheckConstraint("page_from IS NULL OR page_from > 0", name="ck_evidence_page_from"),
        CheckConstraint("page_to IS NULL OR page_to > 0", name="ck_evidence_page_to"),
        CheckConstraint(
            "page_from IS NULL OR page_to IS NULL OR page_to >= page_from",
            name="ck_evidence_page_order",
        ),
    )

    fact_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("facts.id", ondelete="CASCADE"),
        index=True,
    )
    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="RESTRICT"),
        index=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
    )
    page_from: Mapped[int | None]
    page_to: Mapped[int | None]
    quote_text: Mapped[str | None] = mapped_column(Text)
    evidence_role: Mapped[EvidenceRole] = mapped_column(
        enum_type(EvidenceRole, "evidence_role"),
        default=EvidenceRole.SUPPORTS,
        nullable=False,
    )
    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        enum_type(ExtractionMethod, "evidence_extraction_method"),
        nullable=False,
    )
    reviewer_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    reviewer_comment: Mapped[str | None] = mapped_column(Text)

    fact: Mapped[Fact] = relationship(back_populates="evidences")
