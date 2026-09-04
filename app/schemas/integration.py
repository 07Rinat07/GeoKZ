from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.project_info import SupportedLanguage
from app.integrations.types import SyncMode


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
