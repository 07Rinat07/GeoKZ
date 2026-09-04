import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.project_info import SupportedLanguage
from app.integrations.contracts import ExternalDataConnector, ExternalRecordEnvelope
from app.integrations.errors import ConnectorConfigurationError, ExternalSourceProtocolError


@dataclass(frozen=True, slots=True)
class EgovDatasetConfig:
    source_code: str
    dataset: str
    version: str
    record_type: str
    identity_fields: tuple[str, ...]
    language: SupportedLanguage | None = None
    page_size: int = 500

    def __post_init__(self) -> None:
        if not self.identity_fields:
            raise ValueError("identity_fields must contain at least one field")
        if self.page_size < 1 or self.page_size > 10_000:
            raise ValueError("page_size must be between 1 and 10000")


class EgovOpenDataConnector(ExternalDataConnector):
    """Универсальный connector к API v4 портала data.egov.kz."""

    BASE_URL = "https://data.egov.kz"

    def __init__(
        self,
        config: EgovDatasetConfig,
        *,
        api_key: str | None,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._api_key = api_key.strip() if api_key else None
        self._timeout_seconds = timeout_seconds
        self._client = client

    @property
    def source_code(self) -> str:
        return self._config.source_code

    async def check_availability(self) -> bool:
        response = await self._request(
            f"/meta/{self._config.dataset}/{self._config.version}",
            params=None,
            requires_api_key=False,
        )
        return response.status_code == httpx.codes.OK

    async def get_dataset_version(self) -> str | None:
        return self._config.version

    async def fetch_records(
        self,
        *,
        updated_since: datetime | None = None,
        cursor: str | None = None,
    ):
        del updated_since  # У API нет единого стандартного поля даты изменения для всех наборов.

        if not self._api_key:
            raise ConnectorConfigurationError(
                "Для синхронизации data.egov.kz требуется GEOKZ_EGOV_API_KEY"
            )

        offset = self._parse_cursor(cursor)
        while True:
            source_query = {
                "from": offset,
                "size": self._config.page_size,
            }
            response = await self._request(
                f"/api/v4/{self._config.dataset}/{self._config.version}",
                params={
                    "apiKey": self._api_key,
                    "source": json.dumps(source_query, ensure_ascii=False, separators=(",", ":")),
                },
                requires_api_key=True,
            )
            response.raise_for_status()
            payload = response.json()
            records = self._extract_records(payload)

            for record in records:
                yield ExternalRecordEnvelope(
                    external_id=self._build_external_id(record),
                    record_type=self._config.record_type,
                    raw_payload=record,
                    language=self._config.language,
                )

            if len(records) < self._config.page_size:
                break
            offset += self._config.page_size

    async def _request(
        self,
        path: str,
        *,
        params: dict[str, str] | None,
        requires_api_key: bool,
    ) -> httpx.Response:
        if requires_api_key and not self._api_key:
            raise ConnectorConfigurationError(
                "Для синхронизации data.egov.kz требуется GEOKZ_EGOV_API_KEY"
            )

        if self._client is not None:
            return await self._client.get(path, params=params)

        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self._timeout_seconds,
            follow_redirects=True,
        ) as client:
            return await client.get(path, params=params)

    @staticmethod
    def _extract_records(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            raise ExternalSourceProtocolError(
                "data.egov.kz вернул неожиданный формат: ожидался JSON-массив"
            )
        if not all(isinstance(record, dict) for record in payload):
            raise ExternalSourceProtocolError(
                "data.egov.kz вернул массив с элементами, отличными от JSON-объектов"
            )
        return payload

    def _build_external_id(self, record: dict[str, Any]) -> str:
        values: list[str] = []
        for field in self._config.identity_fields:
            value = record.get(field)
            if value is None or str(value).strip() == "":
                raise ExternalSourceProtocolError(
                    f"В записи data.egov.kz отсутствует обязательное identity-поле: {field}"
                )
            values.append(str(value).strip())
        return "|".join(values)

    @staticmethod
    def _parse_cursor(cursor: str | None) -> int:
        if cursor is None:
            return 0
        try:
            offset = int(cursor)
        except ValueError as error:
            raise ConnectorConfigurationError("Некорректный cursor для data.egov.kz") from error
        if offset < 0:
            raise ConnectorConfigurationError("Cursor не может быть отрицательным")
        return offset
