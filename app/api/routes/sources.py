from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import CurrentPrincipal, require_scientific_writer
from app.application.audit import AuditActor, AuditRevisionService
from app.core.database import get_session
from app.models.enums import AuditAction
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceRead, SourceUpdate

router = APIRouter()


def _source_snapshot(source: Source) -> dict:
    return SourceRead.model_validate(source).model_dump(mode="json")


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    principal: CurrentPrincipal = Depends(require_scientific_writer),
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = Source(**payload.model_dump())
    session.add(source)
    try:
        await session.flush()
        await AuditRevisionService(session).audit_master_change(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.CREATE,
            resource_type="source",
            resource_id=source.id,
            snapshot=_source_snapshot(source),
            reason="create",
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Источник с таким ID уже существует") from error
    await session.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: UUID,
    payload: SourceUpdate,
    principal: CurrentPrincipal = Depends(require_scientific_writer),
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Источник не найден")

    changes = payload.model_dump(exclude_unset=True)
    reason = changes.pop("change_reason")
    if not changes:
        raise HTTPException(status_code=422, detail="No source fields were supplied for update")

    before = _source_snapshot(source)
    for field, value in changes.items():
        setattr(source, field, value)

    try:
        await session.flush()
        after = _source_snapshot(source)
        await AuditRevisionService(session).audit_master_change(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.UPDATE,
            resource_type="source",
            resource_id=source.id,
            snapshot=after,
            reason=reason,
            details={"changed_fields": sorted(changes), "before": before},
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Source update violates data integrity") from error
    await session.refresh(source)
    return source


@router.get("", response_model=list[SourceRead])
async def list_sources(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[Source]:
    result = await session.scalars(
        select(Source).order_by(Source.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result)


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Источник не найден")
    return source
