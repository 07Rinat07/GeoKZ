from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CoreDatasetInstalledStateRead(BaseModel):
    dataset_code: str
    dataset_version: str
    schema_version: int
    manifest_sha256: str
    installed_at: datetime
    file_checksums: dict[str, str]
    item_counts: dict[str, int]


class CoreDatasetStatusResponse(BaseModel):
    dataset_code: str
    bundled_version: str
    schema_version: int
    manifest_sha256: str
    minimum_app_version: str | None
    dependencies: dict[str, str]
    installed: CoreDatasetInstalledStateRead | None
    update_available: bool


class CoreDatasetInstallResponse(BaseModel):
    dataset_code: str
    dataset_version: str
    schema_version: int
    manifest_sha256: str
    installed_at: datetime | None
    item_counts: dict[str, int]
    changed: bool
    dry_run: bool
    message: str = Field(min_length=1)


class CoreDatasetUpdateStatusResponse(BaseModel):
    configured: bool
    state: Literal["DISABLED", "FAILED", "CURRENT", "AVAILABLE", "INCOMPATIBLE"]
    installed_version: str | None
    available_version: str | None
    available_manifest_sha256: str | None
    published_at: str | None
    signature_key_id: str | None
    signature_verified: bool
    compatible: bool
    compatibility_issues: list[str]
    rollback_available: bool
    rollback_version: str | None
    error: str | None


class CoreDatasetUpdateOperationResponse(CoreDatasetInstallResponse):
    operation: Literal["update", "rollback"]
    source_url: str | None
    bundle_sha256: str | None
    signature_key_id: str | None
