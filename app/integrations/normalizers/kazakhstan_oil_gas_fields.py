import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.integrations.errors import ExternalSourceProtocolError


_NAME_ALIASES = (
    "Наименование месторождения",
    "наименование месторождения",
    "name",
    "name_ru",
    "field_name",
    "oil_gas_field_name",
    "deposit_name",
    "mestorozhdenie",
    "mestorozhdenie_name",
)


@dataclass(frozen=True, slots=True)
class NormalizedOilGasField:
    name_ru: str
    match_key: str
    source_field: str

    def as_payload(self) -> dict[str, str | int]:
        return {
            "schema_version": 1,
            "entity_type": "field",
            "name_ru": self.name_ru,
            "match_key": self.match_key,
            "source_field": self.source_field,
        }


def normalize_oil_gas_field_record(record: dict[str, Any]) -> NormalizedOilGasField:
    source_field, raw_name = _extract_name(record)
    name = _clean_display_name(raw_name)
    if not name:
        raise ExternalSourceProtocolError(
            "В записи stat_kgn_117 отсутствует непустое наименование месторождения"
        )
    return NormalizedOilGasField(
        name_ru=name,
        match_key=normalize_entity_name(name),
        source_field=source_field,
    )


def normalize_entity_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    normalized = re.sub(r"[«»\"'`’]+", "", normalized)
    normalized = re.sub(r"[^0-9a-zа-яәғқңөұүһі]+", " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


def _extract_name(record: dict[str, Any]) -> tuple[str, str]:
    normalized_keys = {_normalize_key(key): key for key in record}
    for alias in _NAME_ALIASES:
        actual_key = alias if alias in record else normalized_keys.get(_normalize_key(alias))
        if actual_key is None:
            continue
        value = record.get(actual_key)
        if _is_scalar_name(value):
            return actual_key, str(value)

    usable = [
        (key, str(value))
        for key, value in record.items()
        if _is_scalar_name(value)
    ]
    if len(usable) == 1:
        return usable[0]

    raise ExternalSourceProtocolError(
        "Не удалось однозначно определить поле наименования месторождения stat_kgn_117; "
        "проверьте актуальный mapping ресурса"
    )


def _clean_display_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def _normalize_key(value: str) -> str:
    return "".join(character.casefold() for character in value if character.isalnum())


def _is_scalar_name(value: Any) -> bool:
    return isinstance(value, (str, int, float)) and bool(str(value).strip())
