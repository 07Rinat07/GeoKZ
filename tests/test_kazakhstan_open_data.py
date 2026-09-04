from app.integrations.kazakhstan_open_data import (
    KAZAKHSTAN_OPEN_DATASETS,
    get_kazakhstan_dataset,
)


def test_kazakhstan_registry_contains_official_geology_datasets() -> None:
    codes = {dataset.code for dataset in KAZAKHSTAN_OPEN_DATASETS}

    assert "kz-egov-oil-gas-fields" in codes
    assert "kz-egov-geological-study-licenses" in codes

    fields = get_kazakhstan_dataset("kz-egov-oil-gas-fields")
    assert fields is not None
    assert fields.api_uri == "stat_kgn_117"
    assert fields.version == "v10"
    assert fields.record_type == "oil_gas_field"
    assert fields.official_url.startswith("https://data.egov.kz/")
    assert fields.metadata_url.endswith("/meta/stat_kgn_117/v10")
    assert fields.mapping_url.endswith("/api/v4/mapping/stat_kgn_117/v10")

    licenses = get_kazakhstan_dataset("kz-egov-geological-study-licenses")
    assert licenses is not None
    assert licenses.api_uri == "zher_koinauyn_geologiyalyk_zer2"
    assert licenses.version == "v6"
    assert licenses.record_type == "geological_study_license"
    assert "/api/v4/" in licenses.data_url_template
    assert "/api/detailed/" in licenses.detailed_url_template


def test_kazakhstan_dataset_config_has_trilingual_names() -> None:
    for dataset in KAZAKHSTAN_OPEN_DATASETS:
        assert dataset.name_ru.strip()
        assert dataset.name_kk.strip()
        assert dataset.name_en.strip()
        assert dataset.description_ru.strip()
        assert dataset.description_kk.strip()
        assert dataset.description_en.strip()
        assert dataset.api_uri.strip()
        assert dataset.version.startswith("v")
        assert dataset.sync_interval_hours == 168
