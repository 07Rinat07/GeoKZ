from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import (
    ConfidenceLevel,
    FactCategory,
    FactKind,
    VerificationStatus,
)
from app.schemas.common import ORMModel


class FactCreate(ORMModel):
    external_id: str = Field(min_length=3, max_length=200)
    primary_source_id: UUID
    entity_id: UUID | None = None
    entity_type: str = Field(min_length=2, max_length=80)
    category: FactCategory
    original_text: str = Field(min_length=1)
    normalized_statement: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    figure_number: str | None = None
    table_number: str | None = None
    section_title: str | None = None
    methods: list[str] = Field(default_factory=list)
    fact_kind: FactKind
    valid_time_start: int | None = Field(default=None, ge=1500, le=2100)
    valid_time_end: int | None = Field(default=None, ge=1500, le=2100)
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    needs_human_review: bool = True
    review_reason: str | None = None
    verification_status: VerificationStatus = VerificationStatus.DRAFT
    related_fact_ids: list[str] = Field(default_factory=list)


class FactUpdate(ORMModel):
    normalized_statement: str | None = Field(default=None, min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    figure_number: str | None = None
    table_number: str | None = None
    section_title: str | None = None
    methods: list[str] | None = None
    valid_time_start: int | None = Field(default=None, ge=1500, le=2100)
    valid_time_end: int | None = Field(default=None, ge=1500, le=2100)
    confidence: ConfidenceLevel | None = None
    needs_human_review: bool | None = None
    review_reason: str | None = None
    verification_status: VerificationStatus | None = None
    related_fact_ids: list[str] | None = None
    change_reason: str = Field(min_length=3, max_length=1000)


class FactRead(FactCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
