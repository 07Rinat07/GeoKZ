import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime

from app.integrations.errors import ExternalSourceProtocolError

_LICENSE_TYPE_ALIASES = (
    "Вид лицензии на недропользование",
    "вид лицензии на недропользование",
    "license_type",
    "type_of_license",
    "license_kind",
)
_LICENSE_NUMBER_DATE_ALIASES = (
    "Номер и дата лицензии на недропользование",
    "номер и дата лицензии на недропользование",
    "license_number_date",
    "license_number_and_date",
    "license_number",
    "number_date",
)
_LICENSE_TERM_ALIASES = (
    "Срок лицензии на недропользование",
    "срок лицензии на недропользование",
    "license_term",
    "license_period",
    "term",
)
_BASIS_ALIASES = (
    "Основание выдачи лицензии на недропользование",
    "основание выдачи лицензии на недропользование",
    "license_basis",
    "issue_basis",
    "basis",
)
_AUTHORITY_ALIASES = (
    "Наименование государственного органа, выдавшего лицензию на недропользование",
    "наименование государственного органа, выдавшего лицензию на недропользование",
    "issuing_authority",
    "government_authority",
    "authority",
)
_HOLDER_ALIASES = (
    "Сведения о лице, которому выдана лицензия на недропользование",
    "сведения о лице, которому выдана лицензия на недропользование",
    "license_holder",
    "holder",
    "licensee",
    "recipient",
)

_LICENSE_NUMBER_DATE_RE = re.compile(
    r"(?P<number>.*?)(?:\s+от\s+|\s+from\s+)(?P<date>\d{2}[./-]\d{2}[./-]\d{4})",
    flags=re.IGNORECASE,
)
_DATE_RE = re.compile(r"\b(?P<date>\d{2}[./-]\d{2}[./-]\d{4})\b")
_BIN_RE = re.compile(r"\bБИН\s*[:№]?\s*(?P<bin>\d{12})\b", flags=re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class NormalizedGeologicalStudyLicense:
    license_number: str
    issue_date: str | None
    license_number_date_raw: str
    license_type_raw: str | None
    study_scope_code: str | None
    term_raw: str | None
    basis_raw: str | None
    issuing_authority_raw: str | None
    holder_raw: str | None
    holder_bin: str | None
    source_fields: dict[str, str]

    def as_payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "record_type": "geological_study_license",
            "license_number": self.license_number,
            "issue_date": self.issue_date,
            "license_number_date_raw": self.license_number_date_raw,
            "license_type_raw": self.license_type_raw,
            "study_scope_code": self.study_scope_code,
            "term_raw": self.term_raw,
            "basis_raw": self.basis_raw,
            "issuing_authority_raw": self.issuing_authority_raw,
            "holder_raw": self.holder_raw,
            "holder_bin": self.holder_bin,
            "source_fields": self.source_fields,
        }


def normalize_geological_study_license_record(
    record: dict[str, object],
) -> NormalizedGeologicalStudyLicense:
    number_field, number_date_raw = _extract_required_number_date(record)
    license_number, issue_date = _parse_number_and_date(number_date_raw)
    if not license_number:
        raise ExternalSourceProtocolError(
            "В записи zher_koinauyn_geologiyalyk_zer2 не удалось определить номер лицензии"
        )

    source_fields = {"license_number_date": number_field}

    type_field, license_type = _extract_optional(record, _LICENSE_TYPE_ALIASES)
    if type_field is None:
        type_field, license_type = _find_unique_value(record, _looks_like_license_type)
    if type_field is not None:
        source_fields["license_type"] = type_field

    term_field, term = _extract_optional(record, _LICENSE_TERM_ALIASES)
    if term_field is None:
        term_field, term = _find_unique_value(record, _looks_like_term)
    if term_field is not None:
        source_fields["term"] = term_field

    basis_field, basis = _extract_optional(record, _BASIS_ALIASES)
    if basis_field is None:
        basis_field, basis = _find_unique_value(record, _looks_like_basis)
    if basis_field is not None:
        source_fields["basis"] = basis_field

    authority_field, authority = _extract_optional(record, _AUTHORITY_ALIASES)
    if authority_field is None:
        authority_field, authority = _find_unique_value(record, _looks_like_authority)
    if authority_field is not None:
        source_fields["issuing_authority"] = authority_field

    holder_field, holder = _extract_optional(record, _HOLDER_ALIASES)
    if holder_field is None:
        holder_field, holder = _find_unique_value(record, _looks_like_holder)
    if holder_field is not None:
        source_fields["holder"] = holder_field

    return NormalizedGeologicalStudyLicense(
        license_number=license_number,
        issue_date=issue_date,
        license_number_date_raw=_clean(number_date_raw),
        license_type_raw=_clean_optional(license_type),
        study_scope_code=_study_scope_code(license_type),
        term_raw=_clean_optional(term),
        basis_raw=_clean_optional(basis),
        issuing_authority_raw=_clean_optional(authority),
        holder_raw=_clean_optional(holder),
        holder_bin=_extract_bin(holder),
        source_fields=source_fields,
    )


def _extract_required_number_date(record: dict[str, object]) -> tuple[str, str]:
    field, value = _extract_optional(record, _LICENSE_NUMBER_DATE_ALIASES)
    if field is not None and value is not None:
        return field, value

    matches = [
        (key, text)
        for key, value in record.items()
        if (text := _scalar_text(value)) is not None and _looks_like_license_number_date(text)
    ]
    if len(matches) == 1:
        return matches[0]

    raise ExternalSourceProtocolError(
        "Не удалось однозначно определить поле номера/даты лицензии "
        "zher_koinauyn_geologiyalyk_zer2; проверьте актуальный mapping ресурса"
    )


def _extract_optional(
    record: dict[str, object],
    aliases: tuple[str, ...],
) -> tuple[str | None, str | None]:
    normalized_keys = {_normalize_key(key): key for key in record}
    for alias in aliases:
        actual_key = alias if alias in record else normalized_keys.get(_normalize_key(alias))
        if actual_key is None:
            continue
        value = _scalar_text(record.get(actual_key))
        if value is not None:
            return actual_key, value
    return None, None


def _find_unique_value(
    record: dict[str, object],
    predicate,
) -> tuple[str | None, str | None]:
    matches = []
    for key, value in record.items():
        text = _scalar_text(value)
        if text is not None and predicate(text):
            matches.append((key, text))
    if len(matches) == 1:
        return matches[0]
    return None, None


def _parse_number_and_date(value: str) -> tuple[str, str | None]:
    cleaned = _clean(value)
    match = _LICENSE_NUMBER_DATE_RE.search(cleaned)
    if match is not None:
        number = _clean_license_number(match.group("number"))
        return number, _parse_date(match.group("date"))

    date_match = _DATE_RE.search(cleaned)
    issue_date = _parse_date(date_match.group("date")) if date_match else None
    number_part = cleaned[: date_match.start()] if date_match else cleaned
    return _clean_license_number(number_part), issue_date


def _parse_date(value: str) -> str | None:
    normalized = value.replace("/", ".").replace("-", ".")
    try:
        return datetime.strptime(normalized, "%d.%m.%Y").date().isoformat()
    except ValueError:
        return None


def _clean_license_number(value: str) -> str:
    cleaned = _clean(value)
    cleaned = re.sub(r"\s+$", "", cleaned)
    return cleaned


def _study_scope_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    if "подземн" in normalized and "вод" in normalized:
        return "UNDERGROUND_WATER"
    if "углеводород" in normalized or "увс" in normalized:
        return "HYDROCARBONS"
    if "тверд" in normalized and "полезн" in normalized:
        return "SOLID_MINERALS"
    return None


def _extract_bin(value: str | None) -> str | None:
    if value is None:
        return None
    match = _BIN_RE.search(value)
    return match.group("bin") if match is not None else None


def _looks_like_license_number_date(value: str) -> bool:
    normalized = value.casefold()
    return bool(_DATE_RE.search(value)) and (
        "гин" in normalized or "лицен" in normalized or "№" in value
    )


def _looks_like_license_type(value: str) -> bool:
    normalized = value.casefold()
    return "геолог" in normalized and "изуч" in normalized and "недр" in normalized


def _looks_like_term(value: str) -> bool:
    normalized = value.casefold()
    return bool(re.search(r"\b\d+\s*(год|года|лет|жыл|years?)\b", normalized))


def _looks_like_basis(value: str) -> bool:
    normalized = value.casefold()
    return "заявлен" in normalized or "приказ" in normalized or "основан" in normalized


def _looks_like_authority(value: str) -> bool:
    normalized = value.casefold()
    return "комитет" in normalized or "министер" in normalized


def _looks_like_holder(value: str) -> bool:
    normalized = value.casefold()
    return (
        "бин" in normalized
        or "тоо" in normalized
        or "ао " in normalized
        or normalized.startswith("ип ")
    )


def _scalar_text(value: object) -> str | None:
    if not isinstance(value, (str, int, float)):
        return None
    text = str(value).strip()
    return text or None


def _clean(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def _clean_optional(value: str | None) -> str | None:
    return _clean(value) if value is not None else None


def _normalize_key(value: str) -> str:
    return "".join(character.casefold() for character in value if character.isalnum())
