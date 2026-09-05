from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import CurrentPrincipal, get_current_principal, require_admin
from app.core.database import get_session
from app.models.audit import AuditLog, MasterDataRevision
from app.schemas.audit import AuditLogRead, MasterDataRevisionRead

router = APIRouter()


@router.get("/logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _principal: CurrentPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLog]:
    statement = select(AuditLog)
    if action:
        statement = statement.where(AuditLog.action == action)
    if resource_type:
        statement = statement.where(AuditLog.resource_type == resource_type)
    if resource_id:
        statement = statement.where(AuditLog.resource_id == resource_id)
    statement = statement.order_by(AuditLog.occurred_at.desc()).limit(limit).offset(offset)
    return list(await session.scalars(statement))


@router.get(
    "/revisions/{resource_type}/{resource_id}",
    response_model=list[MasterDataRevisionRead],
)
async def list_master_data_revisions(
    resource_type: Literal["source", "geological_entity", "fact"],
    resource_id: UUID,
    _principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> list[MasterDataRevision]:
    statement = (
        select(MasterDataRevision)
        .where(
            MasterDataRevision.resource_type == resource_type,
            MasterDataRevision.resource_id == resource_id,
        )
        .order_by(MasterDataRevision.revision_number)
    )
    return list(await session.scalars(statement))
