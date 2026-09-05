from datetime import datetime

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
