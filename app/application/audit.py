from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, MasterDataRevision
from app.models.auth import UserAccount
from app.models.enums import AuditAction


@dataclass(frozen=True, slots=True)
class AuditActor:
    user_id: UUID
    username: str
    role: object

    @classmethod
    def from_user(cls, user: UserAccount) -> "AuditActor":
        return cls(user_id=user.id, username=user.username, role=user.role)


@dataclass(slots=True)
class AuditRevisionService:
    session: AsyncSession

    async def append_audit(
        self,
        *,
        actor: AuditActor,
        action: AuditAction,
        resource_type: str,
        resource_id: UUID | str | None,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        record = AuditLog(
            actor_user_id=actor.user_id,
            actor_username=actor.username,
            actor_role=actor.role,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            reason=reason,
            details=jsonable_encoder(details or {}),
        )
        self.session.add(record)
        return record

    async def append_revision(
        self,
        *,
        actor: AuditActor,
        action: AuditAction,
        resource_type: str,
        resource_id: UUID,
        snapshot: dict[str, Any],
        reason: str | None = None,
    ) -> MasterDataRevision:
        await self._lock_resource(resource_type=resource_type, resource_id=resource_id)
        current = await self.session.scalar(
            select(func.max(MasterDataRevision.revision_number)).where(
                MasterDataRevision.resource_type == resource_type,
                MasterDataRevision.resource_id == resource_id,
            )
        )
        revision = MasterDataRevision(
            resource_type=resource_type,
            resource_id=resource_id,
            revision_number=(current or 0) + 1,
            action=action,
            snapshot=jsonable_encoder(snapshot),
            reason=reason,
            actor_user_id=actor.user_id,
            actor_username=actor.username,
            actor_role=actor.role,
        )
        self.session.add(revision)
        return revision

    async def audit_master_change(
        self,
        *,
        actor: AuditActor,
        action: AuditAction,
        resource_type: str,
        resource_id: UUID,
        snapshot: dict[str, Any],
        reason: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        await self.append_revision(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            snapshot=snapshot,
            reason=reason,
        )
        await self.append_audit(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            details=details,
        )

    async def _lock_resource(self, *, resource_type: str, resource_id: UUID) -> None:
        key = f"revision:{resource_type}:{resource_id}"
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": key},
        )
