from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from app.core.project_info import SupportedLanguage


@dataclass(frozen=True, slots=True)
class ExternalRecordEnvelope:
    """Неизменяемое транспортное представление записи внешнего источника."""

    external_id: str
    record_type: str
    raw_payload: dict[str, Any]
    source_updated_at: datetime | None = None
    language: SupportedLanguage | None = None


class ExternalDataConnector(Protocol):
    """Контракт адаптера внешнего открытого источника данных."""

    @property
    def source_code(self) -> str:
        """Стабильный машинный код источника."""
        ...

    async def check_availability(self) -> bool:
        """Проверяет доступность источника без изменения локальных данных."""
        ...

    async def get_dataset_version(self) -> str | None:
        """Возвращает версию/дату набора, если источник её предоставляет."""
        ...

    def fetch_records(
        self,
        *,
        updated_since: datetime | None = None,
        cursor: str | None = None,
    ) -> AsyncIterator[ExternalRecordEnvelope]:
        """Потоково отдаёт RAW-записи для staging-слоя GeoKZ."""
        ...
