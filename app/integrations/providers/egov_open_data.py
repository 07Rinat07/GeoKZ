import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.project_info import SupportedLanguage
from app.integrations.contracts import ExternalDataConnector, ExternalRecordEnvelope
from app.integrations.errors import ConnectorConfigurationError, ExternalSourceProtocolError

_VERSION_PATTERN = re.compile(r"^v(?P<number>\d+)$", flags=re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class EgovDatasetConfig:
    source_code: str
    dataset: str
    version: str | None
    record_type: str
    identity_fields: tuple[str, ...] = ()
    identity_alias_groups: tuple[tuple[str, ...], ...] = ()
    language: SupportedLanguage | None = None
    page_size: int = 500

    def __post_init__(self) -> None:
        if self.page_size < 1 or self.page_size > 10_000:
            raise ValueError("page_size must be between 1 and 10000")
        if self.identity_fields and self.identity_alias_groups:
            raise ValueError("Use identity_fields or identity_alias_groups, not both")
        if any(not group for group in self.identity_alias_groups):
            raise ValueError("identity alias groups must not be empty")
        if self.version is not None and not self.version.strip():
            raise ValueError("version must be a non-empty string or None")

    @property
    def api_uri(self) -> str:
        """Официальный apiUri/index набора data.egov.kz.

        ``dataset`` сохранён внутри connector для обратной совместимости раннего
        v0.2-кода. Во внешних GeoKZ-контрактах используется термин ``api_uri``.
        """

        return self.dataset

    @property
    def version_policy(self) -> str:
        return "PINNED" if self.version is not None else "LATEST_MAPPING"


class EgovOpenDataConnector(ExternalDataConnector):
    """Универсальный connector к API v4 портала data.egov.kz.

    Для стабильных интеграций можно зафиксировать ``version``. Для официальных наборов,
    где паспорт портала не показывает версию в статическом HTML, ``version=None``
    означает безопасное определение последней версии через официальный mapping endpoint.
    Выбранная версия кешируется на время жизни connector и затем используется одинаково
    для metadata, mapping и data requests.
    """

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
        self._resolved_version: str | None = config.version

    @property
    def source_code(self) -> str:
        return self._config.source_code

    async def check_availability(self) -> bool:
        version = await self._resolve_version()
        response = await self._request(
            f"/meta/{self._config.api_uri}/{version}",
            params=None,
            requires_api_key=False,
        )
        return response.status_code == httpx.codes.OK

    async def get_dataset_version(self) -> str | None:
        return await self._resolve_version()

    async def get_metadata(self) -> dict[str, Any]:
        """Получить meta-информацию набора по официальному /meta контракту."""

        version = await self._resolve_version()
        response = await self._request(
            f"/meta/{self._config.api_uri}/{version}",
            params=None,
            requires_api_key=False,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ExternalSourceProtocolError(
                "data.egov.kz metadata имеет неожиданный формат: ожидался JSON-объект"
            )
        return payload

    async def get_mapping(self) -> dict[str, Any]:
        """Получить mapping-схему и типы полей набора data.egov.kz."""

        version = await self._resolve_version()
        response = await self._request(
            f"/api/v4/mapping/{self._config.api_uri}/{version}",
            params=None,
            requires_api_key=False,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ExternalSourceProtocolError(
                "data.egov.kz mapping имеет неожиданный формат: ожидался JSON-объект"
            )
        return payload

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

        version = await self._resolve_version()
        offset = self._parse_cursor(cursor)
        while True:
            source_query = {
                "from": offset,
                "size": self._config.page_size,
            }
            response = await self._request(
                f"/api/v4/{self._config.api_uri}/{version}",
                params={
                    "apiKey": self._api_key,
                    "source": json.dumps(
                        source_query,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
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

    async def _resolve_version(self) -> str:
        if self._resolved_version is not None:
            return self._resolved_version

        response = await self._request(
            f"/api/v4/mapping/{self._config.api_uri}",
            params=None,
            requires_api_key=False,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as error:
            raise ExternalSourceProtocolError(
                "data.egov.kz mapping version discovery вернул невалидный JSON"
            ) from error

        versions = self._extract_mapping_versions(payload, self._config.api_uri)
        if not versions:
            raise ExternalSourceProtocolError(
                "Не удалось определить опубликованную версию набора data.egov.kz "
                f"{self._config.api_uri}; проверьте официальный mapping endpoint"
            )

        self._resolved_version = max(versions, key=self._version_sort_key)
        return self._resolved_version

    @staticmethod
    def _extract_mapping_versions(payload: object, api_uri: str) -> tuple[str, ...]:
        if not isinstance(payload, dict):
            return ()
        dataset = payload.get(api_uri)
        if not isinstance(dataset, dict):
            return ()
        mappings = dataset.get("mappings")
        if not isinstance(mappings, dict):
            return ()
        return tuple(
            version
            for version in mappings
            if isinstance(version, str) and _VERSION_PATTERN.fullmatch(version)
        )

    @staticmethod
    def _version_sort_key(version: str) -> int:
        match = _VERSION_PATTERN.fullmatch(version)
        if match is None:
            raise ExternalSourceProtocolError(
                f"Некорректная версия mapping data.egov.kz: {version}"
            )
        return int(match.group("number"))

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
        if self._config.identity_fields:
            return "|".join(
                self._required_value(record, (field,))
                for field in self._config.identity_fields
            )

        if self._config.identity_alias_groups:
            try:
                return "|".join(
                    self._required_value(record, aliases)
                    for aliases in self._config.identity_alias_groups
                )
            except ExternalSourceProtocolError:
                # Схемы открытых наборов иногда меняют технические имена колонок.
                # Не останавливаем весь импорт: RAW-запись получает детерминированный id.
                pass

        canonical = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    @staticmethod
    def _required_value(record: dict[str, Any], aliases: tuple[str, ...]) -> str:
        normalized_keys = {
            EgovOpenDataConnector._normalize_key(key): key for key in record
        }
        for alias in aliases:
            actual_key = alias if alias in record else normalized_keys.get(
                EgovOpenDataConnector._normalize_key(alias)
            )
            if actual_key is None:
                continue
            value = record.get(actual_key)
            if value is not None and str(value).strip():
                return str(value).strip()
        raise ExternalSourceProtocolError(
            "В записи data.egov.kz отсутствует обязательное identity-поле; "
            f"ожидалось одно из: {', '.join(aliases)}"
        )

    @staticmethod
    def _normalize_key(value: str) -> str:
        return "".join(character.casefold() for character in value if character.isalnum())

    @staticmethod
    def _parse_cursor(cursor: str | None) -> int:
        if cursor is None:
            return 0
        try:
            offset = int(cursor)
        except ValueError as error:
            raise ConnectorConfigurationError(
                "Некорректный cursor для data.egov.kz"
            ) from error
        if offset < 0:
            raise ConnectorConfigurationError("Cursor не может быть отрицательным")
        return offset
