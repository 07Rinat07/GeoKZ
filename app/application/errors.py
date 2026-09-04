class ApplicationError(RuntimeError):
    """Базовая ошибка прикладного слоя GeoKZ."""


class ResourceNotFoundError(ApplicationError):
    """Запрошенный доменный объект не найден."""
