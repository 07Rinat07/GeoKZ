from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import AuditAction, UserRole


class AuditLogRead(BaseModel):
    id: UUID
    occurred_at: datetime
    actor_user_id: UUID | None
    actor_username: str
    actor_role: UserRole
    action: AuditAction
    resource_type: str
    resource_id: str | None
    reason: str | None
    details: dict[str, Any]


class MasterDataRevisionRead(BaseModel):
    id: UUID
    resource_type: str
    resource_id: UUID
    revision_number: int
    action: AuditAction
    snapshot: dict[str, Any]
    reason: str | None
    actor_user_id: UUID | None
    actor_username: str
    actor_role: UserRole
    created_at: datetime
