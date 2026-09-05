from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import CurrentPrincipal, require_scientific_writer
from app.application.audit import AuditActor, AuditRevisionService
from app.core.database import get_session
from app.models.enums import AuditAction, UserRole, VerificationStatus
from app.models.fact import Fact
from app.schemas.fact import FactCreate, FactRead, FactUpdate

router = APIRouter()


def _fact_snapshot(fact: Fact) -> dict:
    return FactRead.model_validate(fact).model_dump(mode="json")


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


@router.post("", response_model=FactRead, status_code=status.HTTP_201_CREATED)
async def create_fact(
    payload: FactCreate,
    principal: CurrentPrincipal = Depends(require_scientific_writer),
    session: AsyncSession = Depends(get_session),
) -> Fact:
    _ensure_verification_permission(payload.verification_status, principal)
    fact = Fact(**payload.model_dump())
    session.add(fact)
    try:
        await session.flush()
        await AuditRevisionService(session).audit_master_change(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.CREATE,
            resource_type="fact",
            resource_id=fact.id,
            snapshot=_fact_snapshot(fact),
            reason="create",
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Факт уже существует либо содержит отсутствующую ссылку",
        ) from error
    await session.refresh(fact)
    return fact


@router.patch("/{fact_id}", response_model=FactRead)
async def update_fact(
    fact_id: UUID,
    payload: FactUpdate,
    principal: CurrentPrincipal = Depends(require_scientific_writer),
    session: AsyncSession = Depends(get_session),
) -> Fact:
    fact = await session.get(Fact, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Факт не найден")

    changes = payload.model_dump(exclude_unset=True)
    reason = changes.pop("change_reason")
    if not changes:
        raise HTTPException(status_code=422, detail="No fact fields were supplied for update")
    if "verification_status" in changes and changes["verification_status"] is not None:
        _ensure_verification_permission(changes["verification_status"], principal)

    before = _fact_snapshot(fact)
    for field, value in changes.items():
        setattr(fact, field, value)

    try:
        await session.flush()
        after = _fact_snapshot(fact)
        await AuditRevisionService(session).audit_master_change(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.UPDATE,
            resource_type="fact",
            resource_id=fact.id,
            snapshot=after,
            reason=reason,
            details={"changed_fields": sorted(changes), "before": before},
        )
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Fact update violates data integrity") from error
    await session.refresh(fact)
    return fact


@router.get("", response_model=list[FactRead])
async def list_facts(
    entity_id: UUID | None = None,
    needs_review: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[Fact]:
    statement = select(Fact)
    if entity_id:
        statement = statement.where(Fact.entity_id == entity_id)
    if needs_review is not None:
        statement = statement.where(Fact.needs_human_review == needs_review)
    statement = statement.order_by(Fact.created_at.desc()).limit(limit).offset(offset)
    return list(await session.scalars(statement))


@router.get("/{fact_id}", response_model=FactRead)
async def get_fact(
    fact_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Fact:
    fact = await session.get(Fact, fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Факт не найден")
    return fact
