from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import AuditAction, UserRole, enum_type


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Append-only record of security-sensitive and scientific write operations."""

    __tablename__ = "audit_logs"

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        index=True,
    )
    actor_username: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_role: Mapped[UserRole] = mapped_column(
        enum_type(UserRole, "audit_actor_role"),
        nullable=False,
    )
    action: Mapped[AuditAction] = mapped_column(
        enum_type(AuditAction, "audit_action"),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(200), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )


class MasterDataRevision(UUIDPrimaryKeyMixin, Base):
    """Immutable snapshot revision for scientific master-data resources."""

    __tablename__ = "master_data_revisions"
    __table_args__ = (
        UniqueConstraint(
            "resource_type",
            "resource_id",
            "revision_number",
            name="uq_master_data_revision_number",
        ),
    )

    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[AuditAction] = mapped_column(
        enum_type(AuditAction, "revision_action"),
        nullable=False,
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        index=True,
    )
    actor_username: Mapped[str] = mapped_column(String(120), nullable=False)
    actor_role: Mapped[UserRole] = mapped_column(
        enum_type(UserRole, "revision_actor_role"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
