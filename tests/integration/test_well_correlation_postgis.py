import os
from decimal import Decimal

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.correlation import WellCorrelationService
from app.models.correlation import WellMarker
from app.models.entity import GeologicalEntity
from app.models.enums import (
    DepthReference,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
    WellType,
)
from app.models.well import Well, WellInterval

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_correlation_uses_real_postgis_and_compares_reservoirs() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            field = GeologicalEntity(
                external_id="it-field-aktau-demo",
                object_type="field",
                name_ru="Интеграционное месторождение",
                name_kk="Интеграциялық кен орны",
                name_en="Integration Field",
                verification_status=VerificationStatus.VERIFIED,
            )
            well_entity_a = GeologicalEntity(
                external_id="it-well-entity-a",
                object_type="well",
                name_ru="Скважина A",
                verification_status=VerificationStatus.VERIFIED,
            )
            well_entity_b = GeologicalEntity(
                external_id="it-well-entity-b",
                object_type="well",
                name_ru="Скважина B",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([field, well_entity_a, well_entity_b])
            await session.flush()

            reference_well = Well(
                external_id="it-well-a",
                entity_id=well_entity_a.id,
                object_entity_id=field.id,
                name="A-1",
                well_type=WellType.EXPLORATION,
                total_depth_m=Decimal("3200.0"),
                location=WKTElement("POINT(51.168420 43.652341)", srid=4326),
                verification_status=VerificationStatus.VERIFIED,
            )
            compared_well = Well(
                external_id="it-well-b",
                entity_id=well_entity_b.id,
                object_entity_id=field.id,
                name="B-1",
                well_type=WellType.EXPLORATION,
                total_depth_m=Decimal("3250.0"),
                location=WKTElement("POINT(51.180000 43.652341)", srid=4326),
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([reference_well, compared_well])
            await session.flush()

            session.add_all(
                [
                    WellMarker(
                        well_id=reference_well.id,
                        marker_code="R1",
                        marker_type="stratigraphic",
                        name_ru="Репер R1",
                        depth_m=Decimal("2451.600"),
                        depth_reference=DepthReference.TVDSS,
                        tvdss_m=Decimal("2451.600"),
                        confidence_percent=Decimal("95.0"),
                        verification_status=VerificationStatus.VERIFIED,
                    ),
                    WellMarker(
                        well_id=compared_well.id,
                        marker_code="R1",
                        marker_type="stratigraphic",
                        name_ru="Репер R1",
                        depth_m=Decimal("2470.000"),
                        depth_reference=DepthReference.TVDSS,
                        tvdss_m=Decimal("2470.000"),
                        confidence_percent=Decimal("92.0"),
                        verification_status=VerificationStatus.VERIFIED,
                    ),
                    WellInterval(
                        external_id="it-well-a-j2",
                        well_id=reference_well.id,
                        top_depth_m=Decimal("2450.000"),
                        base_depth_m=Decimal("2478.000"),
                        depth_reference=DepthReference.TVDSS,
                        local_horizon="J-II",
                        lithologies=["sandstone"],
                        porosity_percent=Decimal("17.4"),
                        permeability_md=Decimal("124.0"),
                        net_pay_m=Decimal("18.2"),
                        fluid_type=FluidType.OIL,
                        hydrocarbon_status=HydrocarbonStatus.TESTED_FLOW,
                        verification_status=VerificationStatus.VERIFIED,
                    ),
                    WellInterval(
                        external_id="it-well-b-j2",
                        well_id=compared_well.id,
                        top_depth_m=Decimal("2471.000"),
                        base_depth_m=Decimal("2492.000"),
                        depth_reference=DepthReference.TVDSS,
                        local_horizon="j-ii",
                        lithologies=["sandstone", "siltstone"],
                        porosity_percent=Decimal("15.8"),
                        permeability_md=Decimal("83.0"),
                        net_pay_m=Decimal("12.7"),
                        fluid_type=FluidType.MIXED,
                        hydrocarbon_status=HydrocarbonStatus.LOG_INTERPRETATION,
                        verification_status=VerificationStatus.VERIFIED,
                    ),
                ]
            )
            await session.flush()

            result = await WellCorrelationService(session).compare(
                reference_well_id=reference_well.id,
                well_ids=[compared_well.id],
                language="ru",
            )

            assert len(result.columns) == 2
            compared_column = next(
                column for column in result.columns if column.well.id == compared_well.id
            )
            assert compared_column.distance_from_reference_m is not None
            assert 800 < compared_column.distance_from_reference_m < 1100

            marker_difference = result.marker_differences[0]
            assert marker_difference.marker_code == "R1"
            assert marker_difference.comparable is True
            assert marker_difference.depth_reference == DepthReference.TVDSS
            assert marker_difference.delta_m == Decimal("18.400")

            reservoir_difference = result.reservoir_differences[0]
            assert reservoir_difference.horizon == "J-II"
            assert reservoir_difference.comparable_thickness is True
            assert reservoir_difference.reference_thickness_m == Decimal("28.000")
            assert reservoir_difference.compared_thickness_m == Decimal("21.000")
            assert reservoir_difference.thickness_delta_m == Decimal("-7.000")
            assert reservoir_difference.net_pay_delta_m == Decimal("-5.5")
            assert reservoir_difference.lithology_changed is True
            assert reservoir_difference.fluid_changed is True
            assert reservoir_difference.hydrocarbon_status_changed is True

            await session.rollback()
    finally:
        await engine.dispose()
