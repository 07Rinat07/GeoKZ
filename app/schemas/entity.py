from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import GeometryStatus, VerificationStatus
from app.schemas.common import ORMModel


class GeologicalEntityCreate(ORMModel):
    external_id: str = Field(min_length=3, max_length=200)
    object_type: str = Field(min_length=2, max_length=80)
    parent_id: UUID | None = None
    name_ru: str = Field(min_length=2, max_length=500)
    name_kk: str | None = None
    name_en: str | None = None
    description: str | None = None
    geological_context: dict = Field(default_factory=dict)
    geometry_status: GeometryStatus = GeometryStatus.UNKNOWN
    geometry_source_id: UUID | None = None
    verification_status: VerificationStatus = VerificationStatus.DRAFT


class GeologicalEntityUpdate(ORMModel):
    name_ru: str | None = Field(default=None, min_length=2, max_length=500)
    name_kk: str | None = None
    name_en: str | None = None
    description: str | None = None
    geological_context: dict | None = None
    geometry_status: GeometryStatus | None = None
    geometry_source_id: UUID | None = None
    verification_status: VerificationStatus | None = None
    change_reason: str = Field(min_length=3, max_length=1000)


class GeologicalEntityRead(GeologicalEntityCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
