from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.coordinate_resolution import CoordinateResolutionService
from app.application.crs_registry import OrganizationCrsRegistryService
from app.application.errors import (
    CoordinateResolutionError,
    CrsDefinitionConflictError,
    CrsDefinitionNotConfirmedError,
    CrsDefinitionNotFoundError,
    CrsDefinitionValidationError,
)
from app.application.spatial_search import SpatialSearchService
from app.core.crs_catalog import get_crs_presets
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.schemas.crs import (
    CrsPresetListResponse,
    OrganizationCrsDefinitionConfirm,
    OrganizationCrsDefinitionCreate,
    OrganizationCrsDefinitionListResponse,
    OrganizationCrsDefinitionResponse,
    OrganizationCrsDefinitionUpdate,
)
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


@router.get(
    "/crs-definitions",
    response_model=OrganizationCrsDefinitionListResponse,
)
async def list_organization_crs_definitions(
    lang: SupportedLanguage = Query(default="ru"),
    selectable_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> OrganizationCrsDefinitionListResponse:
    return await OrganizationCrsRegistryService(session).list(
        language=lang,
        selectable_only=selectable_only,
    )


@router.post(
    "/crs-definitions",
    response_model=OrganizationCrsDefinitionResponse,
    status_code=201,
)
async def create_organization_crs_definition(
    request: OrganizationCrsDefinitionCreate,
    lang: SupportedLanguage = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> OrganizationCrsDefinitionResponse:
    try:
        return await OrganizationCrsRegistryService(session).create(
            request,
            language=lang,
        )
    except CrsDefinitionConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except CrsDefinitionValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch(
    "/crs-definitions/{definition_id}",
    response_model=OrganizationCrsDefinitionResponse,
)
async def update_organization_crs_definition(
    definition_id: UUID,
    request: OrganizationCrsDefinitionUpdate,
    lang: SupportedLanguage = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> OrganizationCrsDefinitionResponse:
    try:
        return await OrganizationCrsRegistryService(session).update(
            definition_id,
            request,
            language=lang,
        )
    except CrsDefinitionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CrsDefinitionValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post(
    "/crs-definitions/{definition_id}/confirm",
    response_model=OrganizationCrsDefinitionResponse,
)
async def confirm_organization_crs_definition(
    definition_id: UUID,
    request: OrganizationCrsDefinitionConfirm,
    lang: SupportedLanguage = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> OrganizationCrsDefinitionResponse:
    try:
        return await OrganizationCrsRegistryService(session).confirm(
            definition_id,
            request,
            language=lang,
        )
    except CrsDefinitionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CrsDefinitionValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/nearby", response_model=CoordinateNearbySearchResponse)
async def search_nearby_from_coordinate(
    request: CoordinateNearbySearchRequest,
    session: AsyncSession = Depends(get_session),
) -> CoordinateNearbySearchResponse:
    try:
        resolved = await CoordinateResolutionService(session).resolve(
            request.coordinate
        )
    except CrsDefinitionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CrsDefinitionNotConfirmedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (CoordinateResolutionError, CrsDefinitionValidationError) as error:
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
