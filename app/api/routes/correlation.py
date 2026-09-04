from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.correlation import WellCorrelationService
from app.application.correlation_view import WellCrossSectionViewService
from app.application.demo_correlation_workflow import DemoCorrelationWorkflowService
from app.application.errors import (
    CoordinateResolutionError,
    CrsDefinitionNotConfirmedError,
    CrsDefinitionNotFoundError,
    CrsDefinitionValidationError,
    DemoCorrelationSelectionError,
    ResourceNotFoundError,
)
from app.core.database import get_session
from app.schemas.correlation import (
    WellCorrelationRequest,
    WellCorrelationResponse,
    WellCrossSectionViewResponse,
)
from app.schemas.demo_correlation import (
    DemoCorrelationWorkflowRequest,
    DemoCorrelationWorkflowResponse,
)

router = APIRouter()


@router.post("/wells", response_model=WellCorrelationResponse)
async def correlate_selected_wells(
    request: WellCorrelationRequest,
    session: AsyncSession = Depends(get_session),
) -> WellCorrelationResponse:
    service = WellCorrelationService(session)
    try:
        return await service.compare(
            reference_well_id=request.reference_well_id,
            well_ids=request.well_ids,
            language=request.language,
        )
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/wells/view", response_model=WellCrossSectionViewResponse)
async def build_selected_wells_cross_section(
    request: WellCorrelationRequest,
    session: AsyncSession = Depends(get_session),
) -> WellCrossSectionViewResponse:
    service = WellCrossSectionViewService(session)
    try:
        return await service.build(
            reference_well_id=request.reference_well_id,
            well_ids=request.well_ids,
            language=request.language,
        )
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/demo/workflow", response_model=DemoCorrelationWorkflowResponse)
async def run_demo_correlation_workflow(
    request: DemoCorrelationWorkflowRequest,
    session: AsyncSession = Depends(get_session),
) -> DemoCorrelationWorkflowResponse:
    try:
        return await DemoCorrelationWorkflowService(session).run(request)
    except CrsDefinitionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CrsDefinitionNotConfirmedError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (
        CoordinateResolutionError,
        CrsDefinitionValidationError,
        DemoCorrelationSelectionError,
    ) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/wells/{reference_well_id}", response_model=WellCorrelationResponse)
async def correlate_wells(
    reference_well_id: UUID,
    well_id: list[UUID] = Query(default=[]),
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> WellCorrelationResponse:
    service = WellCorrelationService(session)
    try:
        return await service.compare(
            reference_well_id=reference_well_id,
            well_ids=well_id,
            language=lang,
        )
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
