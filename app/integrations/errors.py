class ExternalIntegrationError(RuntimeError):
    """Базовая ошибка внешней интеграции GeoKZ."""


class ConnectorConfigurationError(ExternalIntegrationError):
    """Connector не может работать из-за отсутствующей или неверной конфигурации."""


class ExternalSourceProtocolError(ExternalIntegrationError):
    """Внешний источник вернул данные, не соответствующие ожидаемому контракту."""
