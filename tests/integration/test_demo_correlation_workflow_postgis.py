import os

import pytest
from geoalchemy2.elements import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.demo_data import DEMO_CORRELATION_WELL_PREFIX
from app.main import app
from app.models.entity import GeologicalEntity
from app.models.enums import VerificationStatus, WellType
from app.models.well import Well
from scripts.seed_correlation_demo import seed

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_demo_workflow_discovers_only_synthetic_wells_and_builds_cross_section() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    await seed()

    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            production_entity = GeologicalEntity(
                external_id="it-production-well-near-demo",
                object_type="well",
                name_ru="Production fixture well",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add(production_entity)
            await session.flush()
            production_well = Well(
                external_id="it-production-well-near-demo",
                entity_id=production_entity.id,
                name="PROD-NEAR-DEMO",
                well_type=WellType.PRODUCTION,
                location=WKTElement("POINT(51.168420 43.652341)", srid=4326),
                source_ids=["integration-production-fixture"],
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add(production_well)
            await session.commit()
            production_well_id = production_well.id

            demo_wells = list(
                await session.scalars(
                    select(Well)
                    .where(Well.external_id.like(f"{DEMO_CORRELATION_WELL_PREFIX}%"))
                    .order_by(Well.external_id)
                )
            )
            assert len(demo_wells) == 4

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            discovery_response = await client.post(
                "/api/v1/correlation/demo/workflow",
                json={
                    "coordinate": {
                        "type": "geographic",
                        "latitude": 43.652341,
                        "longitude": 51.168420,
                    },
                    "radius_km": 5,
                    "language": "en",
                    "limit": 10,
                },
            )

            assert discovery_response.status_code == 200, discovery_response.text
            discovery = discovery_response.json()
            assert discovery["synthetic"] is True
            assert discovery["stage"] == "DISCOVERY"
            assert discovery["can_build_cross_section"] is True
            assert discovery["cross_section"] is None
            assert len(discovery["nearby_demo_wells"]) == 4
            assert all(
                item["synthetic"] is True
                and item["well"]["external_id"].startswith(DEMO_CORRELATION_WELL_PREFIX)
                for item in discovery["nearby_demo_wells"]
            )
            discovered_ids = {
                item["well"]["id"] for item in discovery["nearby_demo_wells"]
            }
            assert str(production_well_id) not in discovered_ids

            reference_id = discovery["suggested_reference_well_id"]
            compared_id = next(
                item["well"]["id"]
                for item in discovery["nearby_demo_wells"]
                if item["well"]["id"] != reference_id
            )
            view_response = await client.post(
                "/api/v1/correlation/demo/workflow",
                json={
                    "coordinate": {
                        "type": "geographic",
                        "latitude": 43.652341,
                        "longitude": 51.168420,
                    },
                    "radius_km": 5,
                    "language": "en",
                    "limit": 10,
                    "reference_well_id": reference_id,
                    "well_ids": [compared_id],
                },
            )

            assert view_response.status_code == 200, view_response.text
            workflow = view_response.json()
            assert workflow["stage"] == "CROSS_SECTION_READY"
            assert workflow["selection"]["reference_well_id"] == reference_id
            assert workflow["selection"]["compared_well_ids"] == [compared_id]
            cross_section = workflow["cross_section"]
            assert cross_section is not None
            assert cross_section["depth_axis"]["depth_reference"] == "TVDSS"
            assert len(cross_section["columns"]) == 2
            line_kinds = {line["kind"] for line in cross_section["correlation_lines"]}
            assert "MARKER" in line_kinds
            assert "HORIZON" in line_kinds
            assert all(
                column["well"]["verification_status"] == "DRAFT"
                for column in cross_section["columns"]
            )

            invalid_response = await client.post(
                "/api/v1/correlation/demo/workflow",
                json={
                    "coordinate": {
                        "type": "geographic",
                        "latitude": 43.652341,
                        "longitude": 51.168420,
                    },
                    "radius_km": 5,
                    "language": "en",
                    "limit": 10,
                    "reference_well_id": reference_id,
                    "well_ids": [str(production_well_id)],
                },
            )
            assert invalid_response.status_code == 422
            assert "synthetic/demo" in invalid_response.json()["detail"]
    finally:
        await engine.dispose()
