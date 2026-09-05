from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import CurrentPrincipal, require_admin
from app.application.audit import AuditActor
from app.application.core_dataset import CoreDatasetImportError
from app.application.core_dataset_management import CoreDatasetManagementService
from app.application.core_dataset_update import (
    CoreDatasetRollbackError,
    CoreDatasetUpdateCompatibilityError,
    CoreDatasetUpdateConfigurationError,
    CoreDatasetUpdateError,
    CoreDatasetUpdateService,
    CoreDatasetUpdateTransportError,
)
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.schemas.core_dataset import (
    CoreDatasetInstalledStateRead,
    CoreDatasetInstallResponse,
    CoreDatasetStatusResponse,
    CoreDatasetUpdateOperationResponse,
    CoreDatasetUpdateStatusResponse,
)

router = APIRouter()

_MESSAGES: dict[SupportedLanguage, dict[str, str]] = {
    "ru": {
        "installed": "GeoKZ Core Dataset установлен транзакционно.",
        "unchanged": "Установленная версия GeoKZ Core Dataset уже соответствует manifest.",
        "dry_run": "GeoKZ Core Dataset успешно проверен; изменения в БД не записаны.",
        "update_installed": "Подписанное обновление GeoKZ Core Dataset проверено и установлено.",
        "update_unchanged": "Установленный GeoKZ Core Dataset уже соответствует подписанному обновлению.",
        "update_dry_run": "Подписанное обновление проверено полностью; БД не изменена.",
        "rolled_back": "GeoKZ Core Dataset безопасно возвращён к предыдущему snapshot.",
    },
    "kk": {
        "installed": "GeoKZ Core Dataset транзакциялық түрде орнатылды.",
        "unchanged": "Орнатылған GeoKZ Core Dataset нұсқасы manifest-пен сәйкес келеді.",
        "dry_run": "GeoKZ Core Dataset сәтті тексерілді; дерекқорға өзгеріс жазылған жоқ.",
        "update_installed": "GeoKZ Core Dataset қолтаңбаланған жаңартуы тексеріліп, орнатылды.",
        "update_unchanged": "Орнатылған Core Dataset қолтаңбаланған жаңартумен сәйкес келеді.",
        "update_dry_run": "Қолтаңбаланған жаңарту толық тексерілді; ДҚ өзгертілген жоқ.",
        "rolled_back": "GeoKZ Core Dataset алдыңғы snapshot-қа қауіпсіз қайтарылды.",
    },
    "en": {
        "installed": "GeoKZ Core Dataset was installed transactionally.",
        "unchanged": "The installed GeoKZ Core Dataset already matches the manifest.",
        "dry_run": "GeoKZ Core Dataset validation succeeded; no database changes were written.",
        "update_installed": "The signed GeoKZ Core Dataset update was verified and installed.",
        "update_unchanged": "The installed Core Dataset already matches the signed update.",
        "update_dry_run": "The signed update passed full validation; the database was not changed.",
        "rolled_back": "GeoKZ Core Dataset was safely restored to the previous snapshot.",
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
    _principal: CurrentPrincipal = Depends(require_admin),
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


@router.get("/update/status", response_model=CoreDatasetUpdateStatusResponse)
async def get_core_dataset_update_status(
    _principal: CurrentPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> CoreDatasetUpdateStatusResponse:
    result = await CoreDatasetUpdateService(session).status()
    return CoreDatasetUpdateStatusResponse(
        configured=result.configured,
        state=result.state.value,
        installed_version=result.installed_version,
        available_version=result.available_version,
        available_manifest_sha256=result.available_manifest_sha256,
        published_at=result.published_at,
        signature_key_id=result.signature_key_id,
        signature_verified=result.signature_verified,
        compatible=result.compatible,
        compatibility_issues=list(result.compatibility_issues),
        rollback_available=result.rollback_available,
        rollback_version=result.rollback_version,
        error=result.error,
    )


@router.post("/update/apply", response_model=CoreDatasetUpdateOperationResponse)
async def apply_core_dataset_update(
    dry_run: bool = Query(default=False),
    lang: SupportedLanguage = Query(default="ru"),
    principal: CurrentPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> CoreDatasetUpdateOperationResponse:
    try:
        operation = await CoreDatasetUpdateService(session).apply(
            actor=AuditActor.from_user(principal.user),
            dry_run=dry_run,
        )
    except (CoreDatasetUpdateConfigurationError, CoreDatasetUpdateTransportError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except CoreDatasetUpdateCompatibilityError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (CoreDatasetUpdateError, CoreDatasetImportError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    result = operation.import_result
    if result.dry_run:
        message_key = "update_dry_run"
    elif result.changed:
        message_key = "update_installed"
    else:
        message_key = "update_unchanged"
    return CoreDatasetUpdateOperationResponse(
        operation="update",
        dataset_code=result.dataset_code,
        dataset_version=result.dataset_version,
        schema_version=result.schema_version,
        manifest_sha256=result.manifest_sha256,
        installed_at=result.installed_at,
        item_counts=result.item_counts,
        changed=result.changed,
        dry_run=result.dry_run,
        message=_MESSAGES[lang][message_key],
        source_url=operation.source_url,
        bundle_sha256=operation.bundle_sha256,
        signature_key_id=operation.signature_key_id,
    )


@router.post("/update/rollback", response_model=CoreDatasetUpdateOperationResponse)
async def rollback_core_dataset_update(
    lang: SupportedLanguage = Query(default="ru"),
    principal: CurrentPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> CoreDatasetUpdateOperationResponse:
    try:
        operation = await CoreDatasetUpdateService(session).rollback(
            actor=AuditActor.from_user(principal.user)
        )
    except CoreDatasetRollbackError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (CoreDatasetUpdateError, CoreDatasetImportError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    result = operation.import_result
    return CoreDatasetUpdateOperationResponse(
        operation="rollback",
        dataset_code=result.dataset_code,
        dataset_version=result.dataset_version,
        schema_version=result.schema_version,
        manifest_sha256=result.manifest_sha256,
        installed_at=result.installed_at,
        item_counts=result.item_counts,
        changed=result.changed,
        dry_run=False,
        message=_MESSAGES[lang]["rolled_back"],
        source_url=None,
        bundle_sha256=None,
        signature_key_id=None,
    )
