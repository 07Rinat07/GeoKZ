import json

import httpx
import pytest

from app.integrations.errors import ConnectorConfigurationError
from app.integrations.providers.egov_open_data import EgovDatasetConfig, EgovOpenDataConnector


def _build_client() -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/meta/"):
            return httpx.Response(
                200,
                json={
                    "apiUri": "demo",
                    "nameRu": "Демонстрационный набор",
                    "fields": {"id": {"type": "Int"}, "name": {"type": "String"}},
                },
            )
        if request.url.path.startswith("/api/v4/mapping/"):
            return httpx.Response(
                200,
                json={
                    "demo": {
                        "mappings": {
                            "v1": {
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"},
                                }
                            }
                        }
                    }
                },
            )

        source = json.loads(request.url.params["source"])
        offset = source["from"]
        if offset == 0:
            return httpx.Response(
                200,
                json=[
                    {"id": 1, "name": "Жетыбай"},
                    {"id": 2, "name": "Тенгиз"},
                ],
            )
        return httpx.Response(200, json=[])

    return httpx.AsyncClient(
        base_url="https://data.egov.kz",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_egov_connector_pages_and_builds_stable_ids() -> None:
    async with _build_client() as client:
        connector = EgovOpenDataConnector(
            EgovDatasetConfig(
                source_code="kz-open-data-demo",
                dataset="demo",
                version="v1",
                record_type="deposit",
                identity_fields=("id",),
                language="ru",
                page_size=2,
            ),
            api_key="test-key",
            client=client,
        )

        assert connector._config.api_uri == "demo"
        assert await connector.check_availability() is True
        metadata = await connector.get_metadata()
        mapping = await connector.get_mapping()
        records = [record async for record in connector.fetch_records()]

    assert metadata["apiUri"] == "demo"
    assert mapping["demo"]["mappings"]["v1"]["properties"]["name"]["type"] == "string"
    assert [record.external_id for record in records] == ["1", "2"]
    assert [record.raw_payload["name"] for record in records] == ["Жетыбай", "Тенгиз"]


@pytest.mark.asyncio
async def test_egov_connector_requires_api_key_for_data_sync() -> None:
    async with _build_client() as client:
        connector = EgovOpenDataConnector(
            EgovDatasetConfig(
                source_code="kz-open-data-demo",
                dataset="demo",
                version="v1",
                record_type="deposit",
                identity_fields=("id",),
            ),
            api_key=None,
            client=client,
        )

        with pytest.raises(ConnectorConfigurationError):
            _ = [record async for record in connector.fetch_records()]
