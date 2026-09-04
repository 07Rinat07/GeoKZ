from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.kazakhstan_open_data import (
    KazakhstanDatasetNotFoundError,
    KazakhstanOpenDataService,
)
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.integrations.errors import (
    ConnectorConfigurationError,
    ExternalSourceProtocolError,
)
from app.integrations.kazakhstan_open_data import KAZAKHSTAN_OPEN_DATASETS
from app.models.integration import ExternalDataSource
from app.schemas.integration import (
    ExternalDataSourceRead,
    KazakhstanDatasetCatalogItem,
    KazakhstanDatasetInspectionResponse,
    KazakhstanDatasetSyncResponse,
)

router = APIRouter()


def _localized_name(source: ExternalDataSource, language: str) -> str:
    if language == "kk":
        return source.name_kk
    if language == "en":
        return source.name_en
    return source.name_ru


def _to_read_model(source: ExternalDataSource, language: str) -> ExternalDataSourceRead:
    return ExternalDataSourceRead(
        id=source.id,
        code=source.code,
        name_ru=source.name_ru,
        name_kk=source.name_kk,
        name_en=source.name_en,
        display_name=_localized_name(source, language),
        language=language,
        base_url=source.base_url,
        enabled=source.enabled,
        sync_mode=source.sync_mode,
        sync_interval_hours=source.sync_interval_hours,
        license_name=source.license_name,
        license_url=source.license_url,
        terms_url=source.terms_url,
        dataset_version=source.dataset_version,
        last_sync_started_at=source.last_sync_started_at,
        last_sync_completed_at=source.last_sync_completed_at,
        last_success_at=source.last_success_at,
        last_error_at=source.last_error_at,
        last_error=source.last_error,
    )


def _catalog_display_name(dataset, language: str) -> str:
    return {
        "ru": dataset.name_ru,
        "kk": dataset.name_kk,
        "en": dataset.name_en,
    }[language]


def _catalog_description(dataset, language: str) -> str:
    return {
        "ru": dataset.description_ru,
        "kk": dataset.description_kk,
        "en": dataset.description_en,
    }[language]


@router.get("/sources", response_model=list[ExternalDataSourceRead])
async def list_external_sources(
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
    enabled_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> list[ExternalDataSourceRead]:
    statement = select(ExternalDataSource).order_by(ExternalDataSource.code)
    if enabled_only:
        statement = statement.where(ExternalDataSource.enabled.is_(True))

    sources = list(await session.scalars(statement))
    return [_to_read_model(source, lang) for source in sources]


@router.get(
    "/kazakhstan/catalog",
    response_model=list[KazakhstanDatasetCatalogItem],
)
async def list_kazakhstan_open_datasets(
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[KazakhstanDatasetCatalogItem]:
    registered_codes = set(
        await session.scalars(
            select(ExternalDataSource.code).where(
                ExternalDataSource.code.in_(
                    [dataset.code for dataset in KAZAKHSTAN_OPEN_DATASETS]
                )
            )
        )
    )
    api_key_configured = bool(
        settings.egov_api_key and settings.egov_api_key.get_secret_value().strip()
    )
    return [
        KazakhstanDatasetCatalogItem(
            code=dataset.code,
            name_ru=dataset.name_ru,
            name_kk=dataset.name_kk,
            name_en=dataset.name_en,
            display_name=_catalog_display_name(dataset, lang),
            description=_catalog_description(dataset, lang),
            api_uri=dataset.api_uri,
            version=dataset.version,
            record_type=dataset.record_type,
            official_url=dataset.official_url,
            metadata_url=dataset.metadata_url,
            mapping_url=dataset.mapping_url,
            data_url_template=dataset.data_url_template,
            detailed_url_template=dataset.detailed_url_template,
            sync_interval_hours=dataset.sync_interval_hours,
            api_key_configured=api_key_configured,
            registered=dataset.code in registered_codes,
        )
        for dataset in KAZAKHSTAN_OPEN_DATASETS
    ]


@router.get(
    "/kazakhstan/{code}/schema",
    response_model=KazakhstanDatasetInspectionResponse,
)
async def inspect_kazakhstan_open_dataset(
    code: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> KazakhstanDatasetInspectionResponse:
    try:
        inspection = await KazakhstanOpenDataService(session, settings).inspect(code)
    except KazakhstanDatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Набор данных не найден") from error
    except ExternalSourceProtocolError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка обращения к data.egov.kz: {error}",
        ) from error

    return KazakhstanDatasetInspectionResponse(
        code=inspection.code,
        api_uri=inspection.api_uri,
        version=inspection.version,
        metadata=inspection.metadata,
        mapping=inspection.mapping,
    )


@router.post(
    "/kazakhstan/register",
    response_model=list[ExternalDataSourceRead],
)
async def register_kazakhstan_open_datasets(
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[ExternalDataSourceRead]:
    sources = await KazakhstanOpenDataService(session, settings).register_all()
    return [_to_read_model(source, lang) for source in sources]


@router.post(
    "/kazakhstan/{code}/sync",
    response_model=KazakhstanDatasetSyncResponse,
)
async def sync_kazakhstan_open_dataset(
    code: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> KazakhstanDatasetSyncResponse:
    try:
        summary = await KazakhstanOpenDataService(session, settings).sync(code)
    except KazakhstanDatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Набор данных не найден") from error
    except ConnectorConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ExternalSourceProtocolError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка обращения к data.egov.kz: {error}",
        ) from error

    return KazakhstanDatasetSyncResponse(
        run_id=summary.run_id,
        source_id=summary.source_id,
        status=summary.status,
        records_received=summary.records_received,
        records_created=summary.records_created,
        records_updated=summary.records_updated,
        records_unchanged=summary.records_unchanged,
        records_rejected=summary.records_rejected,
    )
