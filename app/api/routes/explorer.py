from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import ResourceNotFoundError
from app.application.explorer import GeologicalEntityPassportService, TerritoryExplorerService
from app.core.database import get_session
from app.schemas.explorer import GeologicalEntityPassportResponse, TerritoryOverviewResponse

territories_router = APIRouter()
entities_router = APIRouter()


@territories_router.get("/{region_id}/overview", response_model=TerritoryOverviewResponse)
async def get_territory_overview(
    region_id: UUID,
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> TerritoryOverviewResponse:
    service = TerritoryExplorerService(session)
    try:
        return await service.get_overview(region_id, lang)
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@entities_router.get("/{entity_id}/passport", response_model=GeologicalEntityPassportResponse)
async def get_geological_entity_passport(
    entity_id: UUID,
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> GeologicalEntityPassportResponse:
    service = GeologicalEntityPassportService(session)
    try:
        return await service.get_passport(entity_id, lang)
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
