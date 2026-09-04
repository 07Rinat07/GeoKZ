import pytest

from app.integrations.errors import ExternalSourceProtocolError
from app.integrations.normalizers.kazakhstan_oil_gas_fields import (
    normalize_entity_name,
    normalize_oil_gas_field_record,
)


def test_normalizer_accepts_official_russian_label() -> None:
    normalized = normalize_oil_gas_field_record(
        {"Наименование месторождения": "  ЖЕТЫБАЙ  "}
    )

    assert normalized.name_ru == "ЖЕТЫБАЙ"
    assert normalized.match_key == "жетыбай"
    assert normalized.source_field == "Наименование месторождения"


def test_normalizer_accepts_technical_name_alias() -> None:
    normalized = normalize_oil_gas_field_record({"name": "Тенгиз"})

    assert normalized.name_ru == "Тенгиз"
    assert normalized.match_key == "тенгиз"


def test_normalizer_uses_single_scalar_field_as_safe_fallback() -> None:
    normalized = normalize_oil_gas_field_record({"field_001": "Каражанбас"})

    assert normalized.name_ru == "Каражанбас"
    assert normalized.source_field == "field_001"


def test_normalizer_rejects_ambiguous_unknown_schema() -> None:
    with pytest.raises(ExternalSourceProtocolError):
        normalize_oil_gas_field_record({"column_a": "A", "column_b": "B"})


def test_match_key_normalizes_case_quotes_spacing_and_yo() -> None:
    assert normalize_entity_name("  «Ёлочное   Поле» ") == "елочное поле"
