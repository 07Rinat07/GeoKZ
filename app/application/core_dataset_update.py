from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

import httpx
from packaging.version import InvalidVersion, Version
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit import AuditActor, AuditRevisionService
from app.application.core_dataset import (
    CoreDatasetImporter,
    CoreDatasetImportError,
    CoreDatasetImportResult,
)
from app.core.config import Settings, get_settings
from app.core.core_dataset_manifest import CORE_DATASET_SCHEMA_VERSION, validate_core_dataset_bundle
from app.core.core_dataset_updates import (
    CoreDatasetUpdateDescriptor,
    CoreDatasetUpdateDescriptorError,
    CoreDatasetUpdateSignatureError,
    extract_verified_update_bundle,
    inspect_bundle_identity,
    verify_signed_update_descriptor,
)
from app.core.project_info import PROJECT_VERSION
from app.models.core_dataset import CoreDatasetState
from app.models.enums import AuditAction


class CoreDatasetUpdateError(RuntimeError):
    pass


class CoreDatasetUpdateConfigurationError(CoreDatasetUpdateError):
    pass


class CoreDatasetUpdateTransportError(CoreDatasetUpdateError):
    pass


class CoreDatasetUpdateCompatibilityError(CoreDatasetUpdateError):
    pass


class CoreDatasetRollbackError(CoreDatasetUpdateError):
    pass


class CoreDatasetUpdateState(StrEnum):
    DISABLED = "DISABLED"
    FAILED = "FAILED"
    CURRENT = "CURRENT"
    AVAILABLE = "AVAILABLE"
    INCOMPATIBLE = "INCOMPATIBLE"


@dataclass(frozen=True, slots=True)
class CoreDatasetUpdateStatus:
    configured: bool
    state: CoreDatasetUpdateState
    installed_version: str | None
    available_version: str | None
    available_manifest_sha256: str | None
    published_at: str | None
    signature_key_id: str | None
    signature_verified: bool
    compatible: bool
    compatibility_issues: tuple[str, ...]
    rollback_available: bool
    rollback_version: str | None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CoreDatasetUpdateOperationResult:
    operation: str
    import_result: CoreDatasetImportResult
    source_url: str | None
    bundle_sha256: str | None
    signature_key_id: str | None


@dataclass(slots=True)
class CoreDatasetUpdateService:
    session: AsyncSession
    settings: Settings | None = None
    transport: httpx.AsyncBaseTransport | None = None

    def _settings(self) -> Settings:
        return self.settings or get_settings()

    async def status(self) -> CoreDatasetUpdateStatus:
        settings = self._settings()
        installed = await self._installed_state()
        rollback_available, rollback_version = self._rollback_state(installed)
        if not self._is_configured(settings):
            return CoreDatasetUpdateStatus(
                configured=False,
                state=CoreDatasetUpdateState.DISABLED,
                installed_version=installed.dataset_version if installed else None,
                available_version=None,
                available_manifest_sha256=None,
                published_at=None,
                signature_key_id=None,
                signature_verified=False,
                compatible=False,
                compatibility_issues=(
                    "Core Dataset update channel is not configured",
                ),
                rollback_available=rollback_available,
                rollback_version=rollback_version,
            )

        try:
            descriptor = await self._fetch_descriptor(settings)
            issues = await self._compatibility_issues(descriptor, installed)
        except CoreDatasetUpdateError as error:
            return CoreDatasetUpdateStatus(
                configured=True,
                state=CoreDatasetUpdateState.FAILED,
                installed_version=installed.dataset_version if installed else None,
                available_version=None,
                available_manifest_sha256=None,
                published_at=None,
                signature_key_id=None,
                signature_verified=False,
                compatible=False,
                compatibility_issues=(),
                rollback_available=rollback_available,
                rollback_version=rollback_version,
                error=str(error),
            )

        if issues:
            state = CoreDatasetUpdateState.INCOMPATIBLE
        elif installed is not None and installed.manifest_sha256 == descriptor.manifest_sha256:
            state = CoreDatasetUpdateState.CURRENT
        else:
            state = CoreDatasetUpdateState.AVAILABLE

        return CoreDatasetUpdateStatus(
            configured=True,
            state=state,
            installed_version=installed.dataset_version if installed else None,
            available_version=descriptor.dataset_version,
            available_manifest_sha256=descriptor.manifest_sha256,
            published_at=descriptor.published_at.isoformat(),
            signature_key_id=descriptor.key_id,
            signature_verified=True,
            compatible=not issues,
            compatibility_issues=tuple(issues),
            rollback_available=rollback_available,
            rollback_version=rollback_version,
        )

    async def apply(
        self,
        *,
        actor: AuditActor,
        dry_run: bool = False,
    ) -> CoreDatasetUpdateOperationResult:
        settings = self._settings()
        if not self._is_configured(settings):
            raise CoreDatasetUpdateConfigurationError(
                "Core Dataset update channel requires an HTTPS descriptor URL and trusted Ed25519 key"
            )

        descriptor = await self._fetch_descriptor(settings)
        installed = await self._installed_state(for_update=not dry_run)
        issues = await self._compatibility_issues(descriptor, installed)
        if issues:
            raise CoreDatasetUpdateCompatibilityError("; ".join(issues))
        assert installed is not None  # compatibility gate above requires the bundled baseline.

        if installed.manifest_sha256 == descriptor.manifest_sha256:
            result = CoreDatasetImportResult(
                dataset_code=installed.dataset_code,
                dataset_version=installed.dataset_version,
                schema_version=installed.schema_version,
                manifest_sha256=installed.manifest_sha256,
                installed_at=installed.installed_at,
                item_counts=dict(installed.item_counts),
                changed=False,
                dry_run=dry_run,
            )
            return CoreDatasetUpdateOperationResult(
                operation="update",
                import_result=result,
                source_url=settings.core_dataset_update_manifest_url,
                bundle_sha256=descriptor.bundle_sha256,
                signature_key_id=descriptor.key_id,
            )

        bundle_bytes = await self._download_bundle(descriptor, settings)
        manifest_path = extract_verified_update_bundle(
            bundle_bytes,
            descriptor=descriptor,
            cache_root=settings.core_dataset_update_cache_dir,
            max_extracted_bytes=settings.core_dataset_update_max_bytes,
        )

        try:
            if dry_run:
                result = await CoreDatasetImporter(self.session).import_bundle(
                    manifest_path,
                    dry_run=True,
                )
                return CoreDatasetUpdateOperationResult(
                    operation="update",
                    import_result=result,
                    source_url=settings.core_dataset_update_manifest_url,
                    bundle_sha256=descriptor.bundle_sha256,
                    signature_key_id=descriptor.key_id,
                )

            await self._lock_dataset(installed.dataset_code)
            self._save_previous_state(installed)
            installed.last_update_source_url = settings.core_dataset_update_manifest_url
            installed.last_update_bundle_sha256 = descriptor.bundle_sha256
            installed.last_update_key_id = descriptor.key_id
            await AuditRevisionService(self.session).append_audit(
                actor=actor,
                action=AuditAction.INSTALL,
                resource_type="core_dataset",
                resource_id=installed.dataset_code,
                reason="signed_online_update",
                details={
                    "from_version": installed.previous_dataset_version,
                    "to_version": descriptor.dataset_version,
                    "manifest_sha256": descriptor.manifest_sha256,
                    "bundle_sha256": descriptor.bundle_sha256,
                    "key_id": descriptor.key_id,
                    "descriptor_url": settings.core_dataset_update_manifest_url,
                },
            )
            result = await CoreDatasetImporter(self.session).import_bundle(manifest_path)
        except (CoreDatasetImportError, CoreDatasetUpdateDescriptorError):
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise

        return CoreDatasetUpdateOperationResult(
            operation="update",
            import_result=result,
            source_url=settings.core_dataset_update_manifest_url,
            bundle_sha256=descriptor.bundle_sha256,
            signature_key_id=descriptor.key_id,
        )

    async def rollback(self, *, actor: AuditActor) -> CoreDatasetUpdateOperationResult:
        installed = await self._installed_state(for_update=True)
        if installed is None:
            raise CoreDatasetRollbackError("Core Dataset is not installed")
        if not installed.previous_source_path or not installed.previous_manifest_sha256:
            raise CoreDatasetRollbackError("No previous Core Dataset snapshot is available")

        current_path = Path(installed.source_path) if installed.source_path else None
        previous_path = Path(installed.previous_source_path)
        if current_path is None or not current_path.is_file() or not previous_path.is_file():
            raise CoreDatasetRollbackError(
                "Rollback bundle is unavailable on disk; refusing an unverifiable rollback"
            )

        try:
            current_identity = inspect_bundle_identity(current_path)
            previous_identity = inspect_bundle_identity(previous_path)
            previous_bundle = validate_core_dataset_bundle(previous_path)
        except (CoreDatasetUpdateDescriptorError, ValueError) as error:
            raise CoreDatasetRollbackError(str(error)) from error

        if current_identity != previous_identity:
            raise CoreDatasetRollbackError(
                "Safe rollback is blocked because the two Core Dataset snapshots do not contain "
                "the same external_id identity sets; GeoKZ will not hard-delete newer master data"
            )
        if previous_bundle.manifest_sha256 != installed.previous_manifest_sha256:
            raise CoreDatasetRollbackError(
                "Previous Core Dataset manifest checksum no longer matches rollback metadata"
            )

        await self._lock_dataset(installed.dataset_code)
        from_version = installed.dataset_version
        target_version = installed.previous_dataset_version or previous_bundle.manifest.dataset_version
        await AuditRevisionService(self.session).append_audit(
            actor=actor,
            action=AuditAction.INSTALL,
            resource_type="core_dataset",
            resource_id=installed.dataset_code,
            reason="safe_rollback",
            details={
                "from_version": from_version,
                "to_version": target_version,
                "target_manifest_sha256": installed.previous_manifest_sha256,
            },
        )
        self._clear_previous_state(installed)
        installed.last_update_source_url = None
        installed.last_update_bundle_sha256 = None
        installed.last_update_key_id = None
        try:
            result = await CoreDatasetImporter(self.session).import_bundle(previous_path)
        except Exception:
            await self.session.rollback()
            raise

        return CoreDatasetUpdateOperationResult(
            operation="rollback",
            import_result=result,
            source_url=None,
            bundle_sha256=None,
            signature_key_id=None,
        )

    async def _fetch_descriptor(self, settings: Settings) -> CoreDatasetUpdateDescriptor:
        url = settings.core_dataset_update_manifest_url
        if not url:
            raise CoreDatasetUpdateConfigurationError("Core Dataset update descriptor URL is not set")
        if urlparse(url).scheme.lower() != "https":
            raise CoreDatasetUpdateConfigurationError(
                "Core Dataset update descriptor URL must use HTTPS"
            )
        try:
            async with httpx.AsyncClient(
                timeout=settings.external_http_timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise CoreDatasetUpdateTransportError(
                f"Cannot load Core Dataset update descriptor: {error}"
            ) from error
        try:
            return verify_signed_update_descriptor(
                payload,
                settings.core_dataset_update_trusted_public_keys,
            )
        except CoreDatasetUpdateSignatureError as error:
            raise CoreDatasetUpdateError(str(error)) from error
        except CoreDatasetUpdateDescriptorError as error:
            raise CoreDatasetUpdateError(str(error)) from error

    async def _download_bundle(
        self,
        descriptor: CoreDatasetUpdateDescriptor,
        settings: Settings,
    ) -> bytes:
        try:
            async with httpx.AsyncClient(
                timeout=settings.external_http_timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = await client.get(str(descriptor.bundle_url))
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > settings.core_dataset_update_max_bytes:
                    raise CoreDatasetUpdateError("Core Dataset update bundle exceeds download-size limit")
                content = response.content
        except ValueError as error:
            raise CoreDatasetUpdateTransportError(
                "Invalid Content-Length from Core Dataset update server"
            ) from error
        except httpx.HTTPError as error:
            raise CoreDatasetUpdateTransportError(
                f"Cannot download Core Dataset update bundle: {error}"
            ) from error

        if len(content) > settings.core_dataset_update_max_bytes:
            raise CoreDatasetUpdateError("Core Dataset update bundle exceeds download-size limit")
        digest = hashlib.sha256(content).hexdigest()
        if digest != descriptor.bundle_sha256:
            raise CoreDatasetUpdateError(
                "Core Dataset update bundle checksum does not match signed descriptor"
            )
        return content

    async def _compatibility_issues(
        self,
        descriptor: CoreDatasetUpdateDescriptor,
        installed: CoreDatasetState | None,
    ) -> list[str]:
        issues: list[str] = []
        if installed is None:
            issues.append("Install the bundled Core Dataset baseline before online updates")
        elif descriptor.dataset_code != installed.dataset_code:
            issues.append(
                f"dataset_code mismatch: installed={installed.dataset_code}, remote={descriptor.dataset_code}"
            )
        if descriptor.core_dataset_schema_version != CORE_DATASET_SCHEMA_VERSION:
            issues.append(
                "Core Dataset schema mismatch: "
                f"supported={CORE_DATASET_SCHEMA_VERSION}, remote={descriptor.core_dataset_schema_version}"
            )
        if descriptor.minimum_app_version:
            try:
                if Version(PROJECT_VERSION) < Version(descriptor.minimum_app_version):
                    issues.append(
                        f"Application {PROJECT_VERSION} is older than required "
                        f"{descriptor.minimum_app_version}"
                    )
            except InvalidVersion:
                issues.append("Update descriptor contains an invalid minimum_app_version")
        if descriptor.required_database_revision:
            current_revision = await self.session.scalar(text("SELECT version_num FROM alembic_version"))
            if str(current_revision) != descriptor.required_database_revision:
                issues.append(
                    "Database schema mismatch: "
                    f"current={current_revision}, required={descriptor.required_database_revision}"
                )
        return issues

    async def _installed_state(self, *, for_update: bool = False) -> CoreDatasetState | None:
        query = select(CoreDatasetState).where(CoreDatasetState.dataset_code == "geokz-core")
        if for_update:
            query = query.with_for_update()
        return await self.session.scalar(query)

    @staticmethod
    def _is_configured(settings: Settings) -> bool:
        return bool(
            settings.core_dataset_update_manifest_url
            and settings.core_dataset_update_trusted_public_keys
        )

    @staticmethod
    def _rollback_state(installed: CoreDatasetState | None) -> tuple[bool, str | None]:
        if installed is None:
            return False, None
        available = bool(installed.previous_source_path and installed.previous_manifest_sha256)
        return available, installed.previous_dataset_version if available else None

    @staticmethod
    def _save_previous_state(state: CoreDatasetState) -> None:
        state.previous_dataset_version = state.dataset_version
        state.previous_schema_version = state.schema_version
        state.previous_manifest_sha256 = state.manifest_sha256
        state.previous_installed_at = state.installed_at
        state.previous_source_path = state.source_path
        state.previous_file_checksums = dict(state.file_checksums)
        state.previous_item_counts = dict(state.item_counts)

    @staticmethod
    def _clear_previous_state(state: CoreDatasetState) -> None:
        state.previous_dataset_version = None
        state.previous_schema_version = None
        state.previous_manifest_sha256 = None
        state.previous_installed_at = None
        state.previous_source_path = None
        state.previous_file_checksums = None
        state.previous_item_counts = None

    async def _lock_dataset(self, dataset_code: str) -> None:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"core-dataset-update:{dataset_code}"},
        )
