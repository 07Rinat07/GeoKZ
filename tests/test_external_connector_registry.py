import pytest

from app.core.config import Settings
from app.integrations.errors import ExternalConnectorNotSupportedError
from app.integrations.providers.egov_open_data import EgovOpenDataConnector
from app.integrations.registry import ExternalConnectorRegistry


def test_registry_builds_sync_ready_kazakhstan_connector() -> None:
    registry = ExternalConnectorRegistry(Settings(_env_file=None))

    connector = registry.build("kz-egov-oil-gas-fields")

    assert isinstance(connector, EgovOpenDataConnector)
    assert connector.source_code == "kz-egov-oil-gas-fields"


def test_registry_refuses_catalog_only_kazakhstan_source() -> None:
    registry = ExternalConnectorRegistry(Settings(_env_file=None))

    with pytest.raises(ExternalConnectorNotSupportedError, match="typed normalizer"):
        registry.build("kz-egov-solid-mineral-fields")
