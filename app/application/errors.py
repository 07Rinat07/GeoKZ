class ApplicationError(RuntimeError):
    """Базовая ошибка прикладного слоя GeoKZ."""


class ResourceNotFoundError(ApplicationError):
    """Запрошенный доменный объект не найден."""


class CoordinateResolutionError(ApplicationError):
    """Координаты или исходная CRS не могут быть безопасно преобразованы."""


class DemoCorrelationSelectionError(ApplicationError):
    """Выбор скважин не соответствует безопасному demo workflow."""
