from dataclasses import dataclass

from app.core.config import Settings
from app.integrations.contracts import ExternalDataConnector
from app.integrations.errors import ExternalConnectorNotSupportedError
from app.integrations.kazakhstan_open_data import (
    build_kazakhstan_connector,
    get_kazakhstan_dataset,
)


@dataclass(frozen=True, slots=True)
class ExternalConnectorRegistry:
    """Resolves a registered GeoKZ source code to a sync-ready connector implementation."""

    settings: Settings

    def build(self, source_code: str) -> ExternalDataConnector:
        kazakhstan_dataset = get_kazakhstan_dataset(source_code)
        if kazakhstan_dataset is not None:
            if not kazakhstan_dataset.sync_supported:
                raise ExternalConnectorNotSupportedError(
                    f"Источник {source_code} добавлен в официальный каталог GeoKZ, "
                    "но синхронизация пока отключена до реализации typed normalizer "
                    "и review policy"
                )
            return build_kazakhstan_connector(kazakhstan_dataset, self.settings)

        raise ExternalConnectorNotSupportedError(
            f"Для внешнего источника {source_code} connector ещё не зарегистрирован"
        )
