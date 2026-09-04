import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for integration tests",
)


@pytest.mark.asyncio
async def test_kazakhstan_catalog_registers_official_sources() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register_response = await client.post(
            "/api/v1/integrations/kazakhstan/register?lang=ru"
        )
        assert register_response.status_code == 200, register_response.text
        registered = register_response.json()
        registered_codes = {item["code"] for item in registered}
        assert "kz-egov-oil-gas-fields" in registered_codes
        assert "kz-egov-geological-study-licenses" in registered_codes
        assert all(item["sync_mode"] == "AUTOMATIC" for item in registered)
        assert all(item["sync_interval_hours"] == 168 for item in registered)

        catalog_response = await client.get(
            "/api/v1/integrations/kazakhstan/catalog?lang=ru"
        )
        assert catalog_response.status_code == 200, catalog_response.text
        catalog = catalog_response.json()
        by_code = {item["code"]: item for item in catalog}

        fields = by_code["kz-egov-oil-gas-fields"]
        assert fields["api_uri"] == "stat_kgn_117"
        assert fields["version"] == "v10"
        assert fields["registered"] is True
        assert fields["metadata_url"].endswith("/meta/stat_kgn_117/v10")
        assert fields["mapping_url"].endswith("/api/v4/mapping/stat_kgn_117/v10")

        licenses = by_code["kz-egov-geological-study-licenses"]
        assert licenses["api_uri"] == "zher_koinauyn_geologiyalyk_zer2"
        assert licenses["version"] == "v6"
        assert licenses["registered"] is True
        assert "/api/v4/" in licenses["data_url_template"]
        assert "/api/detailed/" in licenses["detailed_url_template"]
