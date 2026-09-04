from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.correlation import WellCorrelationService
from app.application.errors import ResourceNotFoundError
from app.core.database import get_session
from app.schemas.correlation import WellCorrelationResponse

router = APIRouter()


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
