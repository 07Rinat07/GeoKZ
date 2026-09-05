import pytest

from app.integrations.errors import ExternalSourceProtocolError
from app.integrations.normalizers.kazakhstan_geological_study_licenses import (
    normalize_geological_study_license_record,
)


def test_normalizes_official_russian_license_columns() -> None:
    normalized = normalize_geological_study_license_record(
        {
            "Вид лицензии на недропользование": (
                "Геологическое изучение недр (подземные воды)"
            ),
            "Номер и дата лицензии на недропользование": (
                "№1-ГИН(ПВ) от 16.10.2018 г."
            ),
            "Срок лицензии на недропользование": "3 года",
            "Основание выдачи лицензии на недропользование": (
                "Заявление ТОО «Северный Катпар» (исх № 470 от 01.10.2018 г.)"
            ),
            "Наименование государственного органа, выдавшего лицензию на недропользование": (
                "Комитет геологии и недропользования Министерства по инвестициям и развитию РК"
            ),
            "Сведения о лице, которому выдана лицензия на недропользование": (
                "ТОО «Северный Катпар»; БИН: 040940001700"
            ),
        }
    )

    assert normalized.license_number == "№1-ГИН(ПВ)"
    assert normalized.issue_date == "2018-10-16"
    assert normalized.study_scope_code == "UNDERGROUND_WATER"
    assert normalized.term_raw == "3 года"
    assert normalized.holder_bin == "040940001700"
    assert normalized.source_fields["license_number_date"] == (
        "Номер и дата лицензии на недропользование"
    )


def test_normalizes_hydrocarbon_license_and_technical_aliases() -> None:
    normalized = normalize_geological_study_license_record(
        {
            "license_type": "Геологическое изучение недр (углеводородное сырье)",
            "license_number_date": "№ 101-ГИН (УВС) от 02.08.2021 г.",
            "license_term": "3 года",
            "license_basis": "Заявление ТОО «Forum Group Oil»",
            "issuing_authority": "Комитет геологии Министерства экологии",
            "license_holder": "ТОО «Forum Group Oil» БИН 190840002765",
        }
    )

    assert normalized.license_number == "№ 101-ГИН (УВС)"
    assert normalized.issue_date == "2021-08-02"
    assert normalized.study_scope_code == "HYDROCARBONS"
    assert normalized.holder_bin == "190840002765"


def test_falls_back_to_content_when_mapping_technical_names_change() -> None:
    normalized = normalize_geological_study_license_record(
        {
            "col_a": "Геологическое изучение недр (подземные воды)",
            "col_b": "№500-ГИН(ПВ) от 05.09.2026 г.",
            "col_c": "5 лет",
            "col_d": "Заявление заявителя",
            "col_e": "Комитет геологии Министерства промышленности",
            "col_f": "ТОО «TEST HOLDER»; БИН: 123456789012",
        }
    )

    assert normalized.license_number == "№500-ГИН(ПВ)"
    assert normalized.issue_date == "2026-09-05"
    assert normalized.study_scope_code == "UNDERGROUND_WATER"
    assert normalized.holder_bin == "123456789012"
    assert normalized.source_fields["license_number_date"] == "col_b"


def test_rejects_record_when_license_number_date_is_ambiguous() -> None:
    with pytest.raises(ExternalSourceProtocolError, match="mapping"):
        normalize_geological_study_license_record(
            {
                "a": "№1-ГИН(ПВ) от 01.01.2020 г.",
                "b": "№2-ГИН(ПВ) от 02.02.2020 г.",
            }
        )
