import re
import unicodedata

from app.integrations.errors import ExternalSourceProtocolError


def normalize_entity_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    normalized = re.sub(r"[«»\"'`’]+", "", normalized)
    normalized = re.sub(r"[^0-9a-zа-яәғқңөұүһі]+", " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


def extract_field_name(
    record: dict[str, object],
    *,
    aliases: tuple[str, ...],
    dataset_label: str,
) -> tuple[str, str]:
    normalized_keys = {_normalize_key(key): key for key in record}
    for alias in aliases:
        actual_key = alias if alias in record else normalized_keys.get(_normalize_key(alias))
        if actual_key is None:
            continue
        value = record.get(actual_key)
        if _is_scalar_name(value):
            return actual_key, _clean_display_name(str(value))

    usable = [
        (key, _clean_display_name(str(value)))
        for key, value in record.items()
        if _is_scalar_name(value)
    ]
    if len(usable) == 1:
        return usable[0]

    raise ExternalSourceProtocolError(
        f"Не удалось однозначно определить поле наименования месторождения {dataset_label}; "
        "проверьте актуальный mapping ресурса"
    )


def _clean_display_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def _normalize_key(value: str) -> str:
    return "".join(character.casefold() for character in value if character.isalnum())


def _is_scalar_name(value: object) -> bool:
    return isinstance(value, (str, int, float)) and bool(str(value).strip())
