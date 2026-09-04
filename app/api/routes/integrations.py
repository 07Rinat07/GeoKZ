from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.integration import ExternalDataSource
from app.schemas.integration import ExternalDataSourceRead

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
