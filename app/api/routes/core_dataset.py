from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core_dataset import CoreDatasetImportError
from app.application.core_dataset_management import CoreDatasetManagementService
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.schemas.core_dataset import (
    CoreDatasetInstalledStateRead,
    CoreDatasetInstallResponse,
    CoreDatasetStatusResponse,
)

router = APIRouter()

_MESSAGES: dict[SupportedLanguage, dict[str, str]] = {
    "ru": {
        "installed": "GeoKZ Core Dataset установлен транзакционно.",
        "unchanged": "Установленная версия GeoKZ Core Dataset уже соответствует manifest.",
        "dry_run": "GeoKZ Core Dataset успешно проверен; изменения в БД не записаны.",
    },
    "kk": {
        "installed": "GeoKZ Core Dataset транзакциялық түрде орнатылды.",
        "unchanged": "Орнатылған GeoKZ Core Dataset нұсқасы manifest-пен сәйкес келеді.",
        "dry_run": "GeoKZ Core Dataset сәтті тексерілді; дерекқорға өзгеріс жазылған жоқ.",
    },
    "en": {
        "installed": "GeoKZ Core Dataset was installed transactionally.",
        "unchanged": "The installed GeoKZ Core Dataset already matches the manifest.",
        "dry_run": "GeoKZ Core Dataset validation succeeded; no database changes were written.",
    },
}


@router.get("/status", response_model=CoreDatasetStatusResponse)
async def get_core_dataset_status(
    session: AsyncSession = Depends(get_session),
) -> CoreDatasetStatusResponse:
    try:
        result = await CoreDatasetManagementService(session).status()
    except CoreDatasetImportError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    installed = None
    if result.installed is not None:
        installed = CoreDatasetInstalledStateRead(
            dataset_code=result.installed.dataset_code,
            dataset_version=result.installed.dataset_version,
            schema_version=result.installed.schema_version,
            manifest_sha256=result.installed.manifest_sha256,
            installed_at=result.installed.installed_at,
            file_checksums=dict(result.installed.file_checksums),
            item_counts=dict(result.installed.item_counts),
        )

    return CoreDatasetStatusResponse(
        dataset_code=result.dataset_code,
        bundled_version=result.bundled_version,
        schema_version=result.schema_version,
        manifest_sha256=result.manifest_sha256,
        minimum_app_version=result.minimum_app_version,
        dependencies=result.dependencies,
        installed=installed,
        update_available=result.update_available,
    )


@router.post("/install", response_model=CoreDatasetInstallResponse)
async def install_bundled_core_dataset(
    dry_run: bool = Query(default=False),
    lang: SupportedLanguage = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> CoreDatasetInstallResponse:
    try:
        result = await CoreDatasetManagementService(session).install(dry_run=dry_run)
    except CoreDatasetImportError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    message_key = "dry_run" if result.dry_run else ("installed" if result.changed else "unchanged")
    return CoreDatasetInstallResponse(
        dataset_code=result.dataset_code,
        dataset_version=result.dataset_version,
        schema_version=result.schema_version,
        manifest_sha256=result.manifest_sha256,
        installed_at=result.installed_at,
        item_counts=result.item_counts,
        changed=result.changed,
        dry_run=result.dry_run,
        message=_MESSAGES[lang][message_key],
    )
