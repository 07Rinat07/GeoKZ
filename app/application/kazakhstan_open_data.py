from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.external_sync import ExternalSyncService, SyncSummary
from app.application.kazakhstan_field_processing import (
    OIL_GAS_FIELDS_SOURCE_CODE,
    KazakhstanOilGasFieldProcessingService,
    OilGasFieldProcessingSummary,
)
from app.application.kazakhstan_license_processing import (
    GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE,
    GeologicalStudyLicenseProcessingSummary,
    KazakhstanGeologicalStudyLicenseProcessingService,
)
from app.core.config import Settings
from app.integrations.errors import ExternalConnectorNotSupportedError
from app.integrations.kazakhstan_open_data import (
    KAZAKHSTAN_OPEN_DATASETS,
    KazakhstanOpenDataDataset,
    build_kazakhstan_connector,
    get_kazakhstan_dataset,
)
from app.models.integration import ExternalDataSource


class KazakhstanDatasetNotFoundError(LookupError):
    pass


class KazakhstanDatasetProcessingNotSupportedError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class KazakhstanDatasetInspection:
    code: str
    api_uri: str
    version: str
    metadata: dict[str, Any]
    mapping: dict[str, Any]


@dataclass(slots=True)
class KazakhstanOpenDataService:
    session: AsyncSession
    settings: Settings

    async def register_all(self) -> list[ExternalDataSource]:
        sources: list[ExternalDataSource] = []
        for dataset in KAZAKHSTAN_OPEN_DATASETS:
            sources.append(await self.ensure_registered(dataset))
        await self.session.commit()
        return sources

    async def ensure_registered(
        self,
        dataset: KazakhstanOpenDataDataset,
    ) -> ExternalDataSource:
        source = await self.session.scalar(
            select(ExternalDataSource).where(ExternalDataSource.code == dataset.code)
        )
        if source is None:
            source = ExternalDataSource(
                code=dataset.code,
                name_ru=dataset.name_ru,
                name_kk=dataset.name_kk,
                name_en=dataset.name_en,
                base_url="https://data.egov.kz",
                enabled=dataset.enabled_by_default,
                sync_mode=dataset.sync_mode,
                sync_interval_hours=dataset.sync_interval_hours,
                dataset_version=dataset.version,
                source_config={},
            )
            self.session.add(source)

        source.name_ru = dataset.name_ru
        source.name_kk = dataset.name_kk
        source.name_en = dataset.name_en
        source.base_url = "https://data.egov.kz"
        source.sync_interval_hours = dataset.sync_interval_hours
        if dataset.version is not None:
            source.dataset_version = dataset.version
        source.source_config = {
            "provider": "data.egov.kz",
            "api_uri": dataset.api_uri,
            "version": dataset.version,
            "version_policy": dataset.version_policy,
            "record_type": dataset.record_type,
            "official_url": dataset.official_url,
            "metadata_url": dataset.metadata_url,
            "mapping_url": dataset.mapping_url,
            "data_url_template": dataset.data_url_template,
            "detailed_url_template": dataset.detailed_url_template,
            "api_key_env": "GEOKZ_EGOV_API_KEY",
            "sync_supported": dataset.sync_supported,
            "processing_supported": dataset.processing_supported,
        }
        await self.session.flush()
        return source

    async def inspect(self, code: str) -> KazakhstanDatasetInspection:
        dataset = get_kazakhstan_dataset(code)
        if dataset is None:
            raise KazakhstanDatasetNotFoundError(code)

        connector = build_kazakhstan_connector(dataset, self.settings)
        version = await connector.get_dataset_version()
        if version is None:
            raise ExternalConnectorNotSupportedError(
                f"Не удалось определить версию набора {dataset.code}"
            )
        metadata = await connector.get_metadata()
        mapping = await connector.get_mapping()
        return KazakhstanDatasetInspection(
            code=dataset.code,
            api_uri=dataset.api_uri,
            version=version,
            metadata=metadata,
            mapping=mapping,
        )

    async def sync(self, code: str) -> SyncSummary:
        dataset = get_kazakhstan_dataset(code)
        if dataset is None:
            raise KazakhstanDatasetNotFoundError(code)
        if not dataset.sync_supported:
            raise ExternalConnectorNotSupportedError(
                f"Синхронизация {code} пока отключена: сначала требуется typed normalizer "
                "и review policy"
            )

        source = await self.ensure_registered(dataset)
        await self.session.commit()
        connector = build_kazakhstan_connector(dataset, self.settings)
        return await ExternalSyncService(self.session).sync(source.id, connector)

    async def process(
        self,
        code: str,
    ) -> OilGasFieldProcessingSummary | GeologicalStudyLicenseProcessingSummary:
        dataset = get_kazakhstan_dataset(code)
        if dataset is None:
            raise KazakhstanDatasetNotFoundError(code)
        if not dataset.processing_supported:
            raise KazakhstanDatasetProcessingNotSupportedError(code)
        if code == OIL_GAS_FIELDS_SOURCE_CODE:
            return await KazakhstanOilGasFieldProcessingService(self.session).process()
        if code == GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE:
            return await KazakhstanGeologicalStudyLicenseProcessingService(
                self.session
            ).process()
        raise KazakhstanDatasetProcessingNotSupportedError(code)
