import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.core_dataset import (
    CoreDatasetImportResult,
    CoreDatasetImporter,
    CoreDatasetImportError,
)
from app.core.core_dataset_manifest import (
    DEFAULT_CORE_DATASET_MANIFEST,
    CoreDatasetManifestError,
    load_core_dataset_manifest,
)
from app.models.core_dataset import CoreDatasetState


@dataclass(frozen=True, slots=True)
class CoreDatasetStatus:
    dataset_code: str
    bundled_version: str
    schema_version: int
    manifest_sha256: str
    minimum_app_version: str | None
    dependencies: dict[str, str]
    installed: CoreDatasetState | None
    update_available: bool


@dataclass(slots=True)
class CoreDatasetManagementService:
    session: AsyncSession
    manifest_path: Path = DEFAULT_CORE_DATASET_MANIFEST

    async def status(self) -> CoreDatasetStatus:
        try:
            manifest = load_core_dataset_manifest(self.manifest_path)
            manifest_sha256 = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()
        except (CoreDatasetManifestError, OSError) as error:
            raise CoreDatasetImportError(
                f"Bundled Core Dataset manifest is unavailable: {error}"
            ) from error

        installed = await self.session.scalar(
            select(CoreDatasetState).where(
                CoreDatasetState.dataset_code == manifest.dataset_code
            )
        )
        return CoreDatasetStatus(
            dataset_code=manifest.dataset_code,
            bundled_version=manifest.dataset_version,
            schema_version=manifest.schema_version,
            manifest_sha256=manifest_sha256,
            minimum_app_version=manifest.minimum_app_version,
            dependencies=dict(manifest.dependencies),
            installed=installed,
            update_available=(
                installed is None or installed.manifest_sha256 != manifest_sha256
            ),
        )

    async def install(self, *, dry_run: bool = False) -> CoreDatasetImportResult:
        return await CoreDatasetImporter(self.session).import_bundle(
            self.manifest_path,
            dry_run=dry_run,
        )
