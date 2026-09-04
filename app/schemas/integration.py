from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.project_info import SupportedLanguage
from app.integrations.types import SyncMode, SyncRunStatus


class ExternalDataSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_ru: str
    name_kk: str
    name_en: str
    display_name: str
    language: SupportedLanguage
    base_url: str
    enabled: bool
    sync_mode: SyncMode
    sync_interval_hours: int
    license_name: str | None
    license_url: str | None
    terms_url: str | None
    dataset_version: str | None
    last_sync_started_at: datetime | None
    last_sync_completed_at: datetime | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None


class KazakhstanDatasetCatalogItem(BaseModel):
    code: str
    name_ru: str
    name_kk: str
    name_en: str
    display_name: str
    description: str
    api_uri: str
    version: str
    record_type: str
    official_url: str
    metadata_url: str
    mapping_url: str
    data_url_template: str
    detailed_url_template: str
    sync_interval_hours: int
    api_key_required: bool = True
    api_key_configured: bool
    registered: bool


class KazakhstanDatasetInspectionResponse(BaseModel):
    code: str
    api_uri: str
    version: str
    metadata: dict[str, Any]
    mapping: dict[str, Any]


class KazakhstanDatasetSyncResponse(BaseModel):
    run_id: UUID
    source_id: UUID
    status: SyncRunStatus
    records_received: int
    records_created: int
    records_updated: int
    records_unchanged: int
    records_rejected: int


class KazakhstanDatasetProcessingResponse(BaseModel):
    source_id: UUID
    processed: int
    normalized: int
    exact_matches: int
    alias_matches: int
    ambiguous: int
    unmatched: int
    normalization_errors: int
    reviewer_locked: int
