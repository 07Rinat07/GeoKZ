from uuid import UUID


class ExternalIntegrationError(RuntimeError):
    """Базовая ошибка внешней интеграции GeoKZ."""


class ConnectorConfigurationError(ExternalIntegrationError):
    """Connector не может работать из-за отсутствующей или неверной конфигурации."""


class ExternalSourceProtocolError(ExternalIntegrationError):
    """Внешний источник вернул данные, не соответствующие ожидаемому контракту."""


class ExternalConnectorNotSupportedError(ExternalIntegrationError):
    """Для зарегистрированного source code ещё нет connector factory в GeoKZ."""


class ExternalSyncAlreadyRunningError(ExternalIntegrationError):
    """Для источника уже выполняется другой sync run."""

    def __init__(self, source_code: str, run_id: UUID) -> None:
        self.source_code = source_code
        self.run_id = run_id
        super().__init__(
            f"Синхронизация источника {source_code} уже выполняется (run_id={run_id})"
        )
