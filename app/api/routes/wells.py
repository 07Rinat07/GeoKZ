from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.entity import GeologicalEntity
from app.models.subsurface import (
    CoreRun,
    CoreSample,
    WellLogCurve,
    WellLogRun,
    WellTest,
    WellTrajectoryPoint,
)
from app.models.well import Well, WellInterval
from app.schemas.well import (
    CoreRunSummary,
    CoreSampleSummary,
    LocalizedName,
    WellHeader,
    WellIntervalSummary,
    WellLogCurveSummary,
    WellLogRunSummary,
    WellPassportResponse,
    WellTestSummary,
    WellTrajectoryPointSummary,
)

router = APIRouter()


@router.get("/{well_id}/passport", response_model=WellPassportResponse)
async def get_well_passport(
    well_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> WellPassportResponse:
    well = await session.get(Well, well_id)
    if well is None:
        raise HTTPException(status_code=404, detail="Скважина не найдена")

    entity = await session.get(GeologicalEntity, well.entity_id)
    longitude, latitude = (
        await session.execute(
            select(func.ST_X(Well.location), func.ST_Y(Well.location)).where(Well.id == well_id)
        )
    ).one()

    intervals = list(
        await session.scalars(
            select(WellInterval)
            .where(WellInterval.well_id == well_id)
            .order_by(WellInterval.top_depth_m, WellInterval.base_depth_m)
        )
    )
    trajectory = list(
        await session.scalars(
            select(WellTrajectoryPoint)
            .where(WellTrajectoryPoint.well_id == well_id)
            .order_by(WellTrajectoryPoint.station_index)
        )
    )
    log_runs = list(
        await session.scalars(
            select(WellLogRun)
            .where(WellLogRun.well_id == well_id)
            .order_by(WellLogRun.top_depth_m, WellLogRun.name)
        )
    )
    log_run_ids = [log_run.id for log_run in log_runs]
    log_curves = (
        list(
            await session.scalars(
                select(WellLogCurve)
                .where(WellLogCurve.log_run_id.in_(log_run_ids))
                .order_by(WellLogCurve.log_run_id, WellLogCurve.mnemonic_original)
            )
        )
        if log_run_ids
        else []
    )
    tests = list(
        await session.scalars(
            select(WellTest)
            .where(WellTest.well_id == well_id)
            .order_by(WellTest.top_depth_m, WellTest.test_date)
        )
    )
    core_runs = list(
        await session.scalars(
            select(CoreRun)
            .where(CoreRun.well_id == well_id)
            .order_by(CoreRun.top_depth_m)
        )
    )
    core_run_ids = [core_run.id for core_run in core_runs]
    core_samples = (
        list(
            await session.scalars(
                select(CoreSample)
                .where(CoreSample.core_run_id.in_(core_run_ids))
                .order_by(CoreSample.core_run_id, CoreSample.depth_m)
            )
        )
        if core_run_ids
        else []
    )

    return WellPassportResponse(
        well=WellHeader(
            id=well.id,
            external_id=well.external_id,
            name=well.name,
            aliases=well.aliases,
            localized_name=LocalizedName(
                ru=entity.name_ru if entity else well.name,
                kk=entity.name_kk if entity else None,
                en=entity.name_en if entity else None,
            ),
            well_type=well.well_type,
            status=well.status,
            operator=well.operator,
            spud_date=well.spud_date,
            completion_date=well.completion_date,
            total_depth_m=well.total_depth_m,
            longitude=longitude,
            latitude=latitude,
            coordinate_system_original=well.coordinate_system_original,
            coordinate_accuracy=well.coordinate_accuracy,
            object_entity_id=well.object_entity_id,
            verification_status=well.verification_status,
        ),
        intervals=[WellIntervalSummary.model_validate(item) for item in intervals],
        trajectory=[WellTrajectoryPointSummary.model_validate(item) for item in trajectory],
        log_runs=[WellLogRunSummary.model_validate(item) for item in log_runs],
        log_curves=[WellLogCurveSummary.model_validate(item) for item in log_curves],
        tests=[WellTestSummary.model_validate(item) for item in tests],
        core_runs=[CoreRunSummary.model_validate(item) for item in core_runs],
        core_samples=[CoreSampleSummary.model_validate(item) for item in core_samples],
    )
