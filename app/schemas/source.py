from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import AccessLevel, ReliabilityLevel, SourceDocumentType
from app.schemas.common import ORMModel


class SourceCreate(ORMModel):
    external_id: str = Field(min_length=3, max_length=160)
    title: str = Field(min_length=3)
    authors: list[str] = Field(default_factory=list)
    organization: str | None = None
    publication_year: int | None = Field(default=None, ge=1500, le=2100)
    survey_year_start: int | None = Field(default=None, ge=1500, le=2100)
    survey_year_end: int | None = Field(default=None, ge=1500, le=2100)
    document_type: SourceDocumentType
    language: str = "ru"
    territories: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    inventory_number: str | None = None
    doi: str | None = None
    url: str | None = None
    access_date: date | None = None
    access_level: AccessLevel = AccessLevel.LOCAL
    page_count: int | None = Field(default=None, ge=1)
    map_scale: str | None = None
    coordinate_system: str | None = None
    license: str | None = None
    sha256: str | None = Field(default=None, min_length=64, max_length=64)
    reliability_level: ReliabilityLevel
    notes: str | None = None


class SourceRead(SourceCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
