from dataclasses import dataclass

from app.core.config import Settings
from app.integrations.providers.egov_open_data import (
    EgovDatasetConfig,
    EgovOpenDataConnector,
)
from app.integrations.types import SyncMode


@dataclass(frozen=True, slots=True)
class KazakhstanOpenDataDataset:
    code: str
    name_ru: str
    name_kk: str
    name_en: str
    description_ru: str
    description_kk: str
    description_en: str
    api_uri: str
    version: str | None
    record_type: str
    identity_alias_groups: tuple[tuple[str, ...], ...]
    official_url: str
    metadata_url: str
    mapping_url: str
    data_url_template: str
    detailed_url_template: str
    sync_interval_hours: int = 168
    enabled_by_default: bool = True
    sync_mode: SyncMode = SyncMode.AUTOMATIC
    sync_supported: bool = True
    processing_supported: bool = True

    @property
    def version_policy(self) -> str:
        return "PINNED" if self.version is not None else "LATEST_MAPPING"

    def connector_config(self) -> EgovDatasetConfig:
        return EgovDatasetConfig(
            source_code=self.code,
            dataset=self.api_uri,
            version=self.version,
            record_type=self.record_type,
            identity_alias_groups=self.identity_alias_groups,
            language="ru",
            page_size=500,
        )


KAZAKHSTAN_OPEN_DATASETS: tuple[KazakhstanOpenDataDataset, ...] = (
    KazakhstanOpenDataDataset(
        code="kz-egov-oil-gas-fields",
        name_ru="Нефтегазовые месторождения Республики Казахстан",
        name_kk="Қазақстан Республикасының мұнай-газ кен орындары",
        name_en="Oil and gas fields of the Republic of Kazakhstan",
        description_ru=(
            "Официальный перечень нефтегазовых месторождений Республики Казахстан "
            "на портале открытых данных."
        ),
        description_kk=(
            "Ашық деректер порталындағы Қазақстан Республикасының мұнай-газ "
            "кен орындарының ресми тізбесі."
        ),
        description_en=(
            "Official list of oil and gas fields of the Republic of Kazakhstan "
            "published on the Open Data portal."
        ),
        api_uri="stat_kgn_117",
        version="v10",
        record_type="oil_gas_field",
        identity_alias_groups=(
            (
                "Наименование месторождения",
                "наименование месторождения",
                "field_name",
                "name",
                "name_ru",
            ),
        ),
        official_url="https://data.egov.kz/datasets/view?index=stat_kgn_117",
        metadata_url="https://data.egov.kz/meta/stat_kgn_117/v10",
        mapping_url="https://data.egov.kz/api/v4/mapping/stat_kgn_117/v10",
        data_url_template=(
            "https://data.egov.kz/api/v4/stat_kgn_117/v10?source={source}"
        ),
        detailed_url_template=(
            "https://data.egov.kz/api/detailed/stat_kgn_117/v10?source={source}"
        ),
    ),
    KazakhstanOpenDataDataset(
        code="kz-egov-geological-study-licenses",
        name_ru="Лицензии на геологическое изучение недр",
        name_kk="Жер қойнауын геологиялық зерттеуге берілген лицензиялар",
        name_en="Licenses for geological exploration of subsoil",
        description_ru=(
            "Официальный реестр выданных лицензий на геологическое изучение недр "
            "Республики Казахстан."
        ),
        description_kk=(
            "Қазақстан Республикасында жер қойнауын геологиялық зерттеуге берілген "
            "лицензиялардың ресми тізілімі."
        ),
        description_en=(
            "Official register of licenses issued for geological exploration of "
            "subsoil in the Republic of Kazakhstan."
        ),
        api_uri="zher_koinauyn_geologiyalyk_zer2",
        version="v6",
        record_type="geological_study_license",
        identity_alias_groups=(
            (
                "Номер и дата лицензии на недропользование",
                "номер и дата лицензии на недропользование",
                "license_number_date",
                "license_number",
                "number",
            ),
        ),
        official_url=(
            "https://data.egov.kz/datasets/view?index="
            "zher_koinauyn_geologiyalyk_zer2"
        ),
        metadata_url=(
            "https://data.egov.kz/meta/zher_koinauyn_geologiyalyk_zer2/v6"
        ),
        mapping_url=(
            "https://data.egov.kz/api/v4/mapping/"
            "zher_koinauyn_geologiyalyk_zer2/v6"
        ),
        data_url_template=(
            "https://data.egov.kz/api/v4/"
            "zher_koinauyn_geologiyalyk_zer2/v6?source={source}"
        ),
        detailed_url_template=(
            "https://data.egov.kz/api/detailed/"
            "zher_koinauyn_geologiyalyk_zer2/v6?source={source}"
        ),
    ),
    KazakhstanOpenDataDataset(
        code="kz-egov-solid-mineral-fields",
        name_ru="Твердые полезные ископаемые Республики Казахстан",
        name_kk="Қазақстан Республикасының қатты пайдалы қазбалары",
        name_en="Solid mineral deposits of the Republic of Kazakhstan",
        description_ru=(
            "Официальный ежегодно актуализируемый перечень месторождений твердых "
            "полезных ископаемых Комитета геологии. Версия API определяется через "
            "официальный mapping endpoint, поскольку паспорт набора не публикует её "
            "в статическом представлении."
        ),
        description_kk=(
            "Геология комитетінің жыл сайын жаңартылатын қатты пайдалы қазбалар кен "
            "орындарының ресми тізбесі. API нұсқасы ресми mapping endpoint арқылы "
            "анықталады."
        ),
        description_en=(
            "Official annually updated list of solid-mineral deposits published by the "
            "Committee of Geology. The API version is resolved through the official "
            "mapping endpoint."
        ),
        api_uri="stat_kgn_118",
        version=None,
        record_type="solid_mineral_field",
        identity_alias_groups=(
            (
                "Наименование месторождения",
                "наименование месторождения",
                "field_name",
                "deposit_name",
                "name",
                "name_ru",
            ),
        ),
        official_url="https://data.egov.kz/datasets/view?index=stat_kgn_118",
        metadata_url="https://data.egov.kz/meta/stat_kgn_118/{version}",
        mapping_url="https://data.egov.kz/api/v4/mapping/stat_kgn_118/{version}",
        data_url_template=(
            "https://data.egov.kz/api/v4/stat_kgn_118/{version}?source={source}"
        ),
        detailed_url_template=(
            "https://data.egov.kz/api/detailed/stat_kgn_118/{version}?source={source}"
        ),
        enabled_by_default=False,
        sync_mode=SyncMode.MANUAL,
        sync_supported=False,
        processing_supported=False,
    ),
    KazakhstanOpenDataDataset(
        code="kz-egov-groundwater-fields",
        name_ru="Месторождения подземных вод Республики Казахстан",
        name_kk="Қазақстан Республикасының жерасты сулары кен орындары",
        name_en="Groundwater deposits of the Republic of Kazakhstan",
        description_ru=(
            "Официальный ежегодно актуализируемый перечень месторождений подземных вод "
            "Комитета геологии. Версия API определяется через официальный mapping "
            "endpoint до включения синхронизации."
        ),
        description_kk=(
            "Геология комитетінің жыл сайын жаңартылатын жерасты сулары кен орындарының "
            "ресми тізбесі. Синхрондауды қоспас бұрын API нұсқасы ресми mapping endpoint "
            "арқылы анықталады."
        ),
        description_en=(
            "Official annually updated groundwater-deposit list published by the Committee "
            "of Geology. Its API version is resolved through the official mapping endpoint "
            "before synchronization is enabled."
        ),
        api_uri="stat_kgn_120",
        version=None,
        record_type="groundwater_field",
        identity_alias_groups=(
            (
                "Наименование месторождения",
                "наименование месторождения",
                "field_name",
                "deposit_name",
                "name",
                "name_ru",
            ),
        ),
        official_url="https://data.egov.kz/datasets/view?index=stat_kgn_120",
        metadata_url="https://data.egov.kz/meta/stat_kgn_120/{version}",
        mapping_url="https://data.egov.kz/api/v4/mapping/stat_kgn_120/{version}",
        data_url_template=(
            "https://data.egov.kz/api/v4/stat_kgn_120/{version}?source={source}"
        ),
        detailed_url_template=(
            "https://data.egov.kz/api/detailed/stat_kgn_120/{version}?source={source}"
        ),
        enabled_by_default=False,
        sync_mode=SyncMode.MANUAL,
        sync_supported=False,
        processing_supported=False,
    ),
)

_DATASET_BY_CODE = {dataset.code: dataset for dataset in KAZAKHSTAN_OPEN_DATASETS}


def get_kazakhstan_dataset(code: str) -> KazakhstanOpenDataDataset | None:
    return _DATASET_BY_CODE.get(code)


def build_kazakhstan_connector(
    dataset: KazakhstanOpenDataDataset,
    settings: Settings,
) -> EgovOpenDataConnector:
    api_key = (
        settings.egov_api_key.get_secret_value()
        if settings.egov_api_key is not None
        else None
    )
    return EgovOpenDataConnector(
        dataset.connector_config(),
        api_key=api_key,
        timeout_seconds=settings.external_http_timeout_seconds,
    )
