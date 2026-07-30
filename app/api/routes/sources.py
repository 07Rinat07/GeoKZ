from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceRead

router = APIRouter()


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate,
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = Source(**payload.model_dump())
    session.add(source)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Источник с таким ID уже существует") from error
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
