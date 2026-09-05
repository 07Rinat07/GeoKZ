from app.integrations.kazakhstan_open_data import (
    KAZAKHSTAN_OPEN_DATASETS,
    LATEST_MAPPING_VERSION,
    get_kazakhstan_dataset,
)


def test_kazakhstan_registry_contains_official_geology_datasets() -> None:
    codes = {dataset.code for dataset in KAZAKHSTAN_OPEN_DATASETS}

    assert {
        "kz-egov-oil-gas-fields",
        "kz-egov-geological-study-licenses",
        "kz-egov-solid-mineral-fields",
        "kz-egov-groundwater-fields",
    } <= codes

    fields = get_kazakhstan_dataset("kz-egov-oil-gas-fields")
    assert fields is not None
    assert fields.api_uri == "stat_kgn_117"
    assert fields.version == "v10"
    assert fields.version_policy == "PINNED"
    assert fields.pinned_version == "v10"
    assert fields.record_type == "oil_gas_field"
    assert fields.official_url.startswith("https://data.egov.kz/")
    assert fields.metadata_url.endswith("/meta/stat_kgn_117/v10")
    assert fields.mapping_url.endswith("/api/v4/mapping/stat_kgn_117/v10")

    licenses = get_kazakhstan_dataset("kz-egov-geological-study-licenses")
    assert licenses is not None
    assert licenses.api_uri == "zher_koinauyn_geologiyalyk_zer2"
    assert licenses.version == "v6"
    assert licenses.version_policy == "PINNED"
    assert licenses.pinned_version == "v6"
    assert licenses.record_type == "geological_study_license"
    assert "/api/v4/" in licenses.data_url_template
    assert "/api/detailed/" in licenses.detailed_url_template

    solid = get_kazakhstan_dataset("kz-egov-solid-mineral-fields")
    assert solid is not None
    assert solid.api_uri == "stat_kgn_118"
    assert solid.version == LATEST_MAPPING_VERSION
    assert solid.version_policy == LATEST_MAPPING_VERSION
    assert solid.pinned_version is None
    assert solid.sync_supported is False
    assert solid.processing_supported is False

    groundwater = get_kazakhstan_dataset("kz-egov-groundwater-fields")
    assert groundwater is not None
    assert groundwater.api_uri == "stat_kgn_120"
    assert groundwater.version == LATEST_MAPPING_VERSION
    assert groundwater.version_policy == LATEST_MAPPING_VERSION
    assert groundwater.pinned_version is None
    assert groundwater.sync_supported is False
    assert groundwater.processing_supported is False


def test_kazakhstan_dataset_config_has_trilingual_names_and_version_policy() -> None:
    for dataset in KAZAKHSTAN_OPEN_DATASETS:
        assert dataset.name_ru.strip()
        assert dataset.name_kk.strip()
        assert dataset.name_en.strip()
        assert dataset.description_ru.strip()
        assert dataset.description_kk.strip()
        assert dataset.description_en.strip()
        assert dataset.api_uri.strip()
        assert dataset.version == LATEST_MAPPING_VERSION or dataset.version.startswith("v")
        assert dataset.version_policy in {"PINNED", LATEST_MAPPING_VERSION}
        assert dataset.sync_interval_hours == 168
