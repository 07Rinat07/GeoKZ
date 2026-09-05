from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.types import ExternalRecordStatus


class LicenseReviewRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: UUID
    external_id: str
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None
    status: ExternalRecordStatus
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_comment: str | None


class LicenseReviewDecisionRequest(BaseModel):
    # Legacy compatibility only. The authenticated principal is authoritative.
    reviewer: str | None = Field(default=None, min_length=2, max_length=300)
    comment: str | None = Field(default=None, max_length=2000)


class LicenseReviewRejectRequest(BaseModel):
    reviewer: str | None = Field(default=None, min_length=2, max_length=300)
    comment: str = Field(min_length=2, max_length=2000)


class LicenseReviewActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: UUID
    record_status: ExternalRecordStatus
    reviewed_by: str
    reviewed_at: datetime
    review_comment: str | None
