import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pyproj import Transformer

from app.main import app

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_confirmed_registered_crs_can_drive_spatial_coordinate_resolution() -> None:
    code = f"it-grid-{uuid4().hex[:12]}"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/spatial/crs-definitions?lang=ru",
            json={
                "code": code,
                "name_ru": "Интеграционная локальная сетка",
                "name_kk": "Интеграциялық жергілікті тор",
                "name_en": "Integration local grid",
                "definition_kind": "EPSG",
                "definition": "EPSG:32639",
                "default_axis_order": "x_easting_y_northing",
                "source_reference": "Integration test fixture; explicit CRS metadata",
            },
        )
        assert create_response.status_code == 201, create_response.text
        created = create_response.json()
        assert created["is_confirmed"] is False
        assert created["selectable"] is False

        transformer = Transformer.from_crs(
            "EPSG:4326",
            "EPSG:32639",
            always_xy=True,
        )
        easting, northing = transformer.transform(51.168420, 43.652341)
        coordinate_payload = {
            "coordinate": {
                "type": "projected",
                "x": easting,
                "y": northing,
                "registered_crs_code": code,
            },
            "radius_km": 1,
            "language": "ru",
            "limit": 5,
        }

        unconfirmed_response = await client.post(
            "/api/v1/spatial/nearby",
            json=coordinate_payload,
        )
        assert unconfirmed_response.status_code == 409

        confirm_response = await client.post(
            f"/api/v1/spatial/crs-definitions/{created['id']}/confirm?lang=ru",
            json={
                "confirmed_by": "integration-test",
                "confirmation_note": "Explicit test confirmation",
            },
        )
        assert confirm_response.status_code == 200, confirm_response.text
        confirmed = confirm_response.json()
        assert confirmed["is_confirmed"] is True
        assert confirmed["selectable"] is True

        selectable_response = await client.get(
            "/api/v1/spatial/crs-definitions",
            params={"lang": "en", "selectable_only": "true"},
        )
        assert selectable_response.status_code == 200
        selectable_codes = {
            item["code"] for item in selectable_response.json()["items"]
        }
        assert code in selectable_codes

        nearby_response = await client.post(
            "/api/v1/spatial/nearby",
            json=coordinate_payload,
        )
        assert nearby_response.status_code == 200, nearby_response.text
        resolved = nearby_response.json()["resolved_coordinate"]
        assert resolved["registered_crs_code"] == code
        assert resolved["latitude"] == pytest.approx(43.652341, abs=1e-6)
        assert resolved["longitude"] == pytest.approx(51.168420, abs=1e-6)

        reset_response = await client.patch(
            f"/api/v1/spatial/crs-definitions/{created['id']}?lang=ru",
            json={
                "source_reference": (
                    "Changed integration metadata; confirmation must be repeated"
                )
            },
        )
        assert reset_response.status_code == 200
        reset = reset_response.json()
        assert reset["is_confirmed"] is False
        assert reset["confirmed_by"] is None
        assert reset["confirmed_at"] is None

        blocked_again = await client.post(
            "/api/v1/spatial/nearby",
            json=coordinate_payload,
        )
        assert blocked_again.status_code == 409
