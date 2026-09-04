import os
from decimal import Decimal

import pytest
from geoalchemy2.elements import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
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
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for integration tests",
)


@pytest.mark.asyncio
async def test_cross_section_view_returns_ui_ready_tvdss_contract() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            field = GeologicalEntity(
                external_id="it-cross-section-field",
                object_type="field",
                name_ru="Поле cross-section",
                verification_status=VerificationStatus.VERIFIED,
            )
            reference_entity = GeologicalEntity(
                external_id="it-cross-section-well-entity-a",
                object_type="well",
                name_ru="Cross Section A",
                verification_status=VerificationStatus.VERIFIED,
            )
            compared_entity = GeologicalEntity(
                external_id="it-cross-section-well-entity-b",
                object_type="well",
                name_ru="Cross Section B",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([field, reference_entity, compared_entity])
            await session.flush()

            reference = Well(
                external_id="it-cross-section-well-a",
                entity_id=reference_entity.id,
                object_entity_id=field.id,
                name="CS-A1",
                well_type=WellType.EXPLORATION,
                total_depth_m=Decimal("3200"),
                location=WKTElement("POINT(51.168420 43.652341)", srid=4326),
                verification_status=VerificationStatus.VERIFIED,
            )
            compared = Well(
                external_id="it-cross-section-well-b",
                entity_id=compared_entity.id,
                object_entity_id=field.id,
                name="CS-B1",
                well_type=WellType.EXPLORATION,
                total_depth_m=Decimal("3250"),
                location=WKTElement("POINT(51.180000 43.652341)", srid=4326),
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([reference, compared])
            await session.flush()

            reference_marker = WellMarker(
                well_id=reference.id,
                marker_code="R-CS",
                marker_type="stratigraphic",
                name_ru="Репер CS",
                name_en="CS marker",
                depth_m=Decimal("2451.600"),
                depth_reference=DepthReference.TVDSS,
                tvdss_m=Decimal("2451.600"),
                confidence_percent=Decimal("95"),
                verification_status=VerificationStatus.VERIFIED,
            )
            compared_marker = WellMarker(
                well_id=compared.id,
                marker_code="R-CS",
                marker_type="stratigraphic",
                name_ru="Репер CS",
                name_en="CS marker",
                depth_m=Decimal("2470.000"),
                depth_reference=DepthReference.TVDSS,
                tvdss_m=Decimal("2470.000"),
                confidence_percent=Decimal("92"),
                verification_status=VerificationStatus.VERIFIED,
            )
            reference_interval = WellInterval(
                external_id="it-cross-section-a-j2",
                well_id=reference.id,
                top_depth_m=Decimal("2450.000"),
                base_depth_m=Decimal("2478.000"),
                depth_reference=DepthReference.TVDSS,
                local_horizon="J-II-CS",
                lithologies=["sandstone"],
                net_pay_m=Decimal("18"),
                fluid_type=FluidType.OIL,
                hydrocarbon_status=HydrocarbonStatus.TESTED_FLOW,
                verification_status=VerificationStatus.VERIFIED,
            )
            compared_interval = WellInterval(
                external_id="it-cross-section-b-j2",
                well_id=compared.id,
                top_depth_m=Decimal("2471.000"),
                base_depth_m=Decimal("2492.000"),
                depth_reference=DepthReference.TVDSS,
                local_horizon="j-ii-cs",
                lithologies=["sandstone", "siltstone"],
                net_pay_m=Decimal("13"),
                fluid_type=FluidType.MIXED,
                hydrocarbon_status=HydrocarbonStatus.LOG_INTERPRETATION,
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all(
                [
                    reference_marker,
                    compared_marker,
                    reference_interval,
                    compared_interval,
                ]
            )
            await session.commit()
            reference_id = reference.id
            compared_id = compared.id

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/correlation/wells/view",
                json={
                    "reference_well_id": str(reference_id),
                    "well_ids": [str(compared_id)],
                    "language": "en",
                },
            )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["language"] == "en"
        assert payload["reference_well_id"] == str(reference_id)
        assert payload["title"] == "Well correlation cross-section"
        assert payload["depth_axis"]["depth_reference"] == "TVDSS"
        assert payload["depth_axis"]["direction"] == "DOWN"
        assert payload["has_renderable_data"] is True
        assert [column["column_index"] for column in payload["columns"]] == [0, 1]
        assert payload["columns"][0]["is_reference"] is True
        assert payload["columns"][1]["is_reference"] is False
        assert 800 < payload["columns"][1]["distance_from_reference_m"] < 1100

        line_kinds = {line["kind"] for line in payload["correlation_lines"]}
        assert line_kinds == {"MARKER", "HORIZON"}
        marker_line = next(
            line for line in payload["correlation_lines"] if line["kind"] == "MARKER"
        )
        assert marker_line["key"] == "R-CS"
        assert marker_line["from_depth_m"] == "2451.600"
        assert marker_line["to_depth_m"] == "2470.000"
        horizon_line = next(
            line for line in payload["correlation_lines"] if line["kind"] == "HORIZON"
        )
        assert horizon_line["key"] == "J-II-CS"
    finally:
        await engine.dispose()
