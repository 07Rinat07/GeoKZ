class ApplicationError(RuntimeError):
    """Базовая ошибка прикладного слоя GeoKZ."""


class ResourceNotFoundError(ApplicationError):
    """Запрошенный доменный объект не найден."""


class CoordinateResolutionError(ApplicationError):
    """Координаты или исходная CRS не могут быть безопасно преобразованы."""


class DemoCorrelationSelectionError(ApplicationError):
    """Demo correlation selection is incomplete or outside the discovered synthetic set."""


class CrsDefinitionNotFoundError(ApplicationError):
    """Сохранённое определение CRS не найдено."""


class CrsDefinitionValidationError(ApplicationError):
    """Определение CRS не прошло безопасную проверку PROJ/pyproj."""


class CrsDefinitionNotConfirmedError(ApplicationError):
    """Сохранённая CRS не подтверждена или отключена и не может использоваться."""


class CrsDefinitionConflictError(ApplicationError):
    """Код сохранённой CRS уже используется."""
