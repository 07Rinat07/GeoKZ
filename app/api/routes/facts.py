from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.fact import Fact
from app.schemas.fact import FactCreate, FactRead

router = APIRouter()


@router.post("", response_model=FactRead, status_code=status.HTTP_201_CREATED)
async def create_fact(
    payload: FactCreate,
    session: AsyncSession = Depends(get_session),
) -> Fact:
    fact = Fact(**payload.model_dump())
    session.add(fact)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Факт уже существует либо содержит отсутствующую ссылку",
        ) from error
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
