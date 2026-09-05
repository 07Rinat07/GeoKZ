from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.integrations.types import (
    EntityLinkStatus,
    ExternalRecordStatus,
    MatchMethod,
    SyncMode,
    SyncRunStatus,
)
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import enum_type


class ExternalDataSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_data_sources"
    __table_args__ = (
        CheckConstraint("sync_interval_hours > 0", name="ck_external_sources_sync_interval"),
    )

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name_ru: Mapped[str] = mapped_column(String(500), nullable=False)
    name_kk: Mapped[str] = mapped_column(String(500), nullable=False)
    name_en: Mapped[str] = mapped_column(String(500), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sync_mode: Mapped[SyncMode] = mapped_column(
        enum_type(SyncMode, "external_source_sync_mode"),
        default=SyncMode.MANUAL,
        server_default=SyncMode.MANUAL.value,
        nullable=False,
    )
    sync_interval_hours: Mapped[int] = mapped_column(Integer, default=168, server_default="168")
    license_name: Mapped[str | None] = mapped_column(String(500))
    license_url: Mapped[str | None] = mapped_column(Text)
    terms_url: Mapped[str | None] = mapped_column(Text)
    dataset_version: Mapped[str | None] = mapped_column(String(300))
    cursor: Mapped[str | None] = mapped_column(Text)
    etag: Mapped[str | None] = mapped_column(String(1000))
    last_modified: Mapped[str | None] = mapped_column(String(500))
    last_sync_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    source_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    records: Mapped[list["ExternalRecord"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
    sync_runs: Mapped[list["ExternalSyncRun"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


class ExternalRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_records"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "record_type",
            "external_id",
            name="uq_external_records_identity",
        ),
    )

    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("external_data_sources.id", ondelete="CASCADE"),
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(16), index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[ExternalRecordStatus] = mapped_column(
        enum_type(ExternalRecordStatus, "external_record_status"),
        default=ExternalRecordStatus.STAGED,
        server_default=ExternalRecordStatus.STAGED.value,
        nullable=False,
        index=True,
    )
    is_deleted_upstream: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(300))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[str | None] = mapped_column(Text)

    source: Mapped[ExternalDataSource] = relationship(back_populates="records")
    entity_links: Mapped[list["ExternalEntityLink"]] = relationship(
        back_populates="external_record",
        cascade="all, delete-orphan",
    )


class ExternalSyncRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_sync_runs"

    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("external_data_sources.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[SyncRunStatus] = mapped_column(
        enum_type(SyncRunStatus, "external_sync_run_status"),
        default=SyncRunStatus.RUNNING,
        server_default=SyncRunStatus.RUNNING.value,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_received: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    records_created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    records_unchanged: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    records_rejected: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)
    checkpoint: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    source: Mapped[ExternalDataSource] = relationship(back_populates="sync_runs")


class ExternalEntityLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_entity_links"
    __table_args__ = (
        UniqueConstraint(
            "external_record_id",
            "geological_entity_id",
            name="uq_external_entity_links_pair",
        ),
        CheckConstraint(
            "match_confidence >= 0 AND match_confidence <= 1",
            name="ck_external_entity_links_confidence",
        ),
    )

    external_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("external_records.id", ondelete="CASCADE"),
        index=True,
    )
    geological_entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="CASCADE"),
        index=True,
    )
    match_method: Mapped[MatchMethod] = mapped_column(
        enum_type(MatchMethod, "external_entity_match_method"),
        nullable=False,
    )
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[EntityLinkStatus] = mapped_column(
        enum_type(EntityLinkStatus, "external_entity_link_status"),
        default=EntityLinkStatus.REVIEW_REQUIRED,
        server_default=EntityLinkStatus.REVIEW_REQUIRED.value,
        nullable=False,
        index=True,
    )
    verified_by: Mapped[str | None] = mapped_column(String(300))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[str | None] = mapped_column(Text)

    external_record: Mapped[ExternalRecord] = relationship(back_populates="entity_links")
