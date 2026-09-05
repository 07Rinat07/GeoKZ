import json

import httpx
import pytest

from app.integrations.errors import ConnectorConfigurationError, ExternalSourceProtocolError
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
        assert connector._config.version_policy == "PINNED"
        assert await connector.check_availability() is True
        metadata = await connector.get_metadata()
        mapping = await connector.get_mapping()
        records = [record async for record in connector.fetch_records()]

    assert metadata["apiUri"] == "demo"
    assert mapping["demo"]["mappings"]["v1"]["properties"]["name"]["type"] == "string"
    assert [record.external_id for record in records] == ["1", "2"]
    assert [record.raw_payload["name"] for record in records] == ["Жетыбай", "Тенгиз"]


@pytest.mark.asyncio
async def test_egov_connector_discovers_latest_numeric_mapping_version_once() -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        if request.url.path == "/api/v4/mapping/dynamic":
            return httpx.Response(
                200,
                json={
                    "dynamic": {
                        "mappings": {
                            "v2": {"properties": {}},
                            "v10": {"properties": {}},
                            "preview": {"properties": {}},
                        }
                    }
                },
            )
        if request.url.path == "/meta/dynamic/v10":
            return httpx.Response(200, json={"apiUri": "dynamic", "version": "v10"})
        if request.url.path == "/api/v4/mapping/dynamic/v10":
            return httpx.Response(
                200,
                json={"dynamic": {"mappings": {"v10": {"properties": {}}}}},
            )
        if request.url.path == "/api/v4/dynamic/v10":
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    async with httpx.AsyncClient(
        base_url="https://data.egov.kz",
        transport=httpx.MockTransport(handler),
    ) as client:
        connector = EgovOpenDataConnector(
            EgovDatasetConfig(
                source_code="dynamic-source",
                dataset="dynamic",
                version=None,
                record_type="field",
            ),
            api_key="test-key",
            client=client,
        )

        assert connector._config.version_policy == "LATEST_MAPPING"
        assert await connector.get_dataset_version() == "v10"
        assert await connector.check_availability() is True
        assert (await connector.get_metadata())["version"] == "v10"
        await connector.get_mapping()
        records = [record async for record in connector.fetch_records()]

    assert records == []
    assert requested_paths.count("/api/v4/mapping/dynamic") == 1
    assert "/meta/dynamic/v10" in requested_paths
    assert "/api/v4/mapping/dynamic/v10" in requested_paths
    assert "/api/v4/dynamic/v10" in requested_paths


@pytest.mark.asyncio
async def test_egov_connector_rejects_dynamic_mapping_without_published_version() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"dynamic": {"mappings": {"preview": {"properties": {}}}}},
        )

    async with httpx.AsyncClient(
        base_url="https://data.egov.kz",
        transport=httpx.MockTransport(handler),
    ) as client:
        connector = EgovOpenDataConnector(
            EgovDatasetConfig(
                source_code="dynamic-source",
                dataset="dynamic",
                version=None,
                record_type="field",
            ),
            api_key=None,
            client=client,
        )
        with pytest.raises(ExternalSourceProtocolError, match="опубликованную версию"):
            await connector.get_dataset_version()


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
