from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.entity import GeologicalEntity
from app.schemas.entity import GeologicalEntityCreate, GeologicalEntityRead

router = APIRouter()


@router.post("", response_model=GeologicalEntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    payload: GeologicalEntityCreate,
    session: AsyncSession = Depends(get_session),
) -> GeologicalEntity:
    entity = GeologicalEntity(**payload.model_dump())
    session.add(entity)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Объект с таким ID уже существует") from error
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
