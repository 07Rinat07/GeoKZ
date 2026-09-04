from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.coordinates import CoordinateResolver
from app.application.errors import CoordinateResolutionError
from app.application.spatial_search import SpatialSearchService
from app.core.crs_catalog import get_crs_presets
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.schemas.crs import CrsPresetListResponse
from app.schemas.spatial_search import (
    CoordinateNearbySearchRequest,
    CoordinateNearbySearchResponse,
)

router = APIRouter()


@router.get("/crs-presets", response_model=CrsPresetListResponse)
async def list_crs_presets(
    lang: SupportedLanguage = Query(default="ru"),
) -> CrsPresetListResponse:
    return get_crs_presets(lang)


@router.post("/nearby", response_model=CoordinateNearbySearchResponse)
async def search_nearby_from_coordinate(
    request: CoordinateNearbySearchRequest,
    session: AsyncSession = Depends(get_session),
) -> CoordinateNearbySearchResponse:
    try:
        resolved = CoordinateResolver().resolve(request.coordinate)
    except CoordinateResolutionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    result = await SpatialSearchService(session).search_nearby(
        latitude=resolved.latitude,
        longitude=resolved.longitude,
        radius_km=request.radius_km,
        language=request.language,
        limit=request.limit,
    )
    return CoordinateNearbySearchResponse(
        resolved_coordinate=resolved,
        result=result,
    )
