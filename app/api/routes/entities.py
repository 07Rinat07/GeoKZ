from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import CurrentPrincipal, require_scientific_writer
from app.application.audit import AuditActor, AuditRevisionService
from app.core.database import get_session
from app.models.entity import GeologicalEntity
from app.models.enums import AuditAction, UserRole, VerificationStatus
from app.schemas.entity import (
    GeologicalEntityCreate,
    GeologicalEntityRead,
    GeologicalEntityUpdate,
)

router = APIRouter()


def _entity_snapshot(entity: GeologicalEntity) -> dict:
    return GeologicalEntityRead.model_validate(entity).model_dump(mode="json")


def _ensure_verification_permission(
    verification_status: VerificationStatus,
    principal: CurrentPrincipal,
) -> None:
    if (
        verification_status != VerificationStatus.DRAFT
        and principal.user.role not in {UserRole.EXPERT, UserRole.ADMIN}
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only expert or admin may create or set a non-DRAFT verification status",
        )


@router.post("", response_model=GeologicalEntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: GeologicalEntityCreate,
    principal: CurrentPrincipal = Depends(require_scientific_writer),
    session: AsyncSession = Depends(get_session),
) -> GeologicalEntity:
    _ensure_verification_permission(payload.verification_status, principal)
    entity = GeologicalEntity(**payload.model_dump())
    session.add(entity)
    try:
        await session.flush()
        await AuditRevisionService(session).audit_master_change(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.CREATE,
            resource_type="geological_entity",
            resource_id=entity.id,
            snapshot=_entity_snapshot(entity),
            reason="create",
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Объект с таким ID уже существует") from error
    await session.refresh(entity)
    return entity


@router.patch("/{entity_id}", response_model=GeologicalEntityRead)
async def update_entity(
    entity_id: UUID,
    payload: GeologicalEntityUpdate,
    principal: CurrentPrincipal = Depends(require_scientific_writer),
    session: AsyncSession = Depends(get_session),
) -> GeologicalEntity:
    entity = await session.get(GeologicalEntity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Геологический объект не найден")

    changes = payload.model_dump(exclude_unset=True)
    reason = changes.pop("change_reason")
    if not changes:
        raise HTTPException(status_code=422, detail="No entity fields were supplied for update")
    if "verification_status" in changes and changes["verification_status"] is not None:
        _ensure_verification_permission(changes["verification_status"], principal)

    before = _entity_snapshot(entity)
    for field, value in changes.items():
        setattr(entity, field, value)

    try:
        await session.flush()
        after = _entity_snapshot(entity)
        await AuditRevisionService(session).audit_master_change(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.UPDATE,
            resource_type="geological_entity",
            resource_id=entity.id,
            snapshot=after,
            reason=reason,
            details={"changed_fields": sorted(changes), "before": before},
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Entity update violates data integrity") from error
    await session.refresh(entity)
    return entity


@router.get("", response_model=list[GeologicalEntityRead])
async def list_entities(
    q: str | None = Query(default=None, min_length=2),
    object_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[GeologicalEntity]:
    statement = select(GeologicalEntity)
    if q:
        statement = statement.where(GeologicalEntity.name_ru.ilike(f"%{q}%"))
    if object_type:
        statement = statement.where(GeologicalEntity.object_type == object_type)
    statement = statement.order_by(GeologicalEntity.name_ru).limit(limit).offset(offset)
    return list(await session.scalars(statement))


@router.get("/{entity_id}", response_model=GeologicalEntityRead)
async def get_entity(
    entity_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> GeologicalEntity:
    entity = await session.get(GeologicalEntity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Геологический объект не найден")
    return entity
