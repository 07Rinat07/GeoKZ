from uuid import uuid4

import pytest
from geoalchemy2.elements import WKTElement
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionFactory
from app.main import app
from app.models.entity import GeologicalEntity
from app.models.enums import VerificationStatus, WellType
from app.models.well import Well


@pytest.mark.asyncio
async def test_spatial_nearby_api_returns_well_at_input_location() -> None:
    suffix = uuid4().hex
    async with AsyncSessionFactory() as session:
        field = GeologicalEntity(
            external_id=f"it-spatial-field-{suffix}",
            object_type="field",
            name_ru="Интеграционный объект пространственного поиска",
            verification_status=VerificationStatus.VERIFIED,
        )
        well_entity = GeologicalEntity(
            external_id=f"it-spatial-well-entity-{suffix}",
            object_type="well",
            name_ru="Интеграционная скважина пространственного поиска",
            verification_status=VerificationStatus.VERIFIED,
        )
        session.add_all([field, well_entity])
        await session.flush()

        well = Well(
            external_id=f"it-spatial-well-{suffix}",
            entity_id=well_entity.id,
            object_entity_id=field.id,
            name=f"IT-SPATIAL-{suffix[:8]}",
            well_type=WellType.EXPLORATION,
            location=WKTElement("POINT(51.168420 43.652341)", srid=4326),
            verification_status=VerificationStatus.VERIFIED,
        )
        session.add(well)
        await session.commit()
        expected_external_id = well.external_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/spatial/nearby",
            json={
                "coordinate": {
                    "type": "geographic",
                    "latitude": "43,652341",
                    "longitude": "51.168420",
                    "crs": "EPSG:4326",
                },
                "radius_km": 2,
                "language": "ru",
                "limit": 50,
            },
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["resolved_coordinate"]["latitude"] == pytest.approx(43.652341)
    assert payload["resolved_coordinate"]["longitude"] == pytest.approx(51.168420)

    nearby_wells = payload["result"]["nearby_wells"]
    found = next(
        item for item in nearby_wells if item["well"]["external_id"] == expected_external_id
    )
    assert found["distance_m"] == pytest.approx(0.0, abs=0.1)
    assert found["passport_path"].startswith("/api/v1/wells/")
