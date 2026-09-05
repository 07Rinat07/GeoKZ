import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_system_versions_reports_database_and_core_dataset_versions() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/system/versions")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["application_version"]
    assert payload["database_schema_version"] == "20260905_0011"
    assert payload["bundled_core_dataset_version"] == "2026.09.0-bootstrap"
    assert payload["bundled_core_dataset_schema_version"] == 1
    assert "installed_core_dataset_version" in payload
    assert "installed_core_dataset_schema_version" in payload
    assert "installed_core_dataset_at" in payload
