from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.project_info import SupportedLanguage
from app.integrations.types import (
    EntityLinkStatus,
    ExternalRecordStatus,
    FieldReviewActionCode,
    FieldReviewMatchStatus,
    MatchMethod,
    SyncMode,
    SyncRunStatus,
)
from app.models.enums import VerificationStatus


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


class FieldReviewLinkRead(BaseModel):
    link_id: UUID
    entity_id: UUID
    entity_name_ru: str
    match_method: MatchMethod
    match_confidence: float
    status: EntityLinkStatus
    verified_by: str | None
    review_comment: str | None


class FieldReviewRecordRead(BaseModel):
    record_id: UUID
    external_id: str
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None
    status: ExternalRecordStatus
    links: list[FieldReviewLinkRead]


class FieldReviewActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: FieldReviewActionCode
    label: str
    method: str
    path: str
    enabled: bool
    disabled_reason: str | None
    required_fields: list[str]
    optional_fields: list[str]


class FieldReviewCandidateViewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    link_id: UUID
    entity_id: UUID
    entity_display_name: str
    entity_verification_status: VerificationStatus
    match_method: MatchMethod
    match_confidence: float
    status: EntityLinkStatus
    verified_by: str | None
    review_comment: str | None
    actions: list[FieldReviewActionRead]


class FieldReviewRecordViewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: UUID
    external_id: str
    display_name: str
    status: ExternalRecordStatus
    matching_status: FieldReviewMatchStatus
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None
    candidates: list[FieldReviewCandidateViewRead]
    actions: list[FieldReviewActionRead]


class FieldReviewQueueViewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_code: str
    language: SupportedLanguage
    title: str
    policy_note: str
    total_pending: int
    returned_count: int
    limit: int
    offset: int
    has_more: bool
    records: list[FieldReviewRecordViewRead]


class FieldReviewDecisionRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=300)
    comment: str | None = Field(default=None, max_length=2000)


class FieldReviewRejectRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=300)
    comment: str = Field(min_length=2, max_length=2000)


class FieldReviewManualLinkRequest(BaseModel):
    entity_id: UUID
    reviewer: str = Field(min_length=2, max_length=300)
    comment: str | None = Field(default=None, max_length=2000)


class FieldReviewCreateDraftRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=300)
    comment: str | None = Field(default=None, max_length=2000)
    name_ru: str | None = Field(default=None, min_length=1, max_length=500)
    name_kk: str | None = Field(default=None, min_length=1, max_length=500)
    name_en: str | None = Field(default=None, min_length=1, max_length=500)


class FieldReviewActionResponse(BaseModel):
    record_id: UUID
    record_status: ExternalRecordStatus
    link_id: UUID
    link_status: EntityLinkStatus
    entity_id: UUID
    entity_verification_status: VerificationStatus
