from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.external_sync import ExternalSyncService, SyncSummary
from app.core.config import Settings
from app.integrations.kazakhstan_open_data import (
    KAZAKHSTAN_OPEN_DATASETS,
    KazakhstanOpenDataDataset,
    build_kazakhstan_connector,
    get_kazakhstan_dataset,
)
from app.integrations.types import SyncMode
from app.models.integration import ExternalDataSource


class KazakhstanDatasetNotFoundError(LookupError):
    pass


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
                enabled=True,
                sync_mode=SyncMode.AUTOMATIC,
                sync_interval_hours=dataset.sync_interval_hours,
                dataset_version=dataset.version,
                source_config={},
            )
            self.session.add(source)

        source.name_ru = dataset.name_ru
        source.name_kk = dataset.name_kk
        source.name_en = dataset.name_en
        source.base_url = "https://data.egov.kz"
        source.sync_mode = SyncMode.AUTOMATIC
        source.sync_interval_hours = dataset.sync_interval_hours
        source.dataset_version = dataset.version
        source.source_config = {
            "provider": "data.egov.kz",
            "api_uri": dataset.api_uri,
            "version": dataset.version,
            "record_type": dataset.record_type,
            "official_url": dataset.official_url,
            "metadata_url": dataset.metadata_url,
            "mapping_url": dataset.mapping_url,
            "data_url_template": dataset.data_url_template,
            "detailed_url_template": dataset.detailed_url_template,
            "api_key_env": "GEOKZ_EGOV_API_KEY",
        }
        await self.session.flush()
        return source

    async def sync(self, code: str) -> SyncSummary:
        dataset = get_kazakhstan_dataset(code)
        if dataset is None:
            raise KazakhstanDatasetNotFoundError(code)

        source = await self.ensure_registered(dataset)
        await self.session.commit()
        connector = build_kazakhstan_connector(dataset, self.settings)
        return await ExternalSyncService(self.session).sync(source.id, connector)
