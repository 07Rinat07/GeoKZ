from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.project_info import SupportedLanguage
from app.schemas.coordinates import ProjectedAxisOrder


class CrsDefinitionKind(StrEnum):
    EPSG = "EPSG"
    WKT = "WKT"
    PROJ = "PROJ"


class CrsPreset(BaseModel):
    code: str
    epsg: int
    coordinate_type: str
    display_name: str
    longitude_range: str | None = None
    default_axis_order: ProjectedAxisOrder | None = None
    requires_source_confirmation: bool = True


class CrsPresetListResponse(BaseModel):
    language: SupportedLanguage
    presets: list[CrsPreset]
    warning: str


class OrganizationCrsDefinitionCreate(BaseModel):
    code: str = Field(
        min_length=3,
        max_length=120,
        pattern=r"^[a-z0-9][a-z0-9._-]+$",
    )
    name_ru: str = Field(min_length=1, max_length=300)
    name_kk: str = Field(min_length=1, max_length=300)
    name_en: str = Field(min_length=1, max_length=300)
    definition_kind: CrsDefinitionKind
    definition: str = Field(min_length=3, max_length=50000)
    default_axis_order: ProjectedAxisOrder
    source_reference: str = Field(min_length=3, max_length=5000)
    notes: str | None = Field(default=None, max_length=5000)


class OrganizationCrsDefinitionUpdate(BaseModel):
    name_ru: str | None = Field(default=None, min_length=1, max_length=300)
    name_kk: str | None = Field(default=None, min_length=1, max_length=300)
    name_en: str | None = Field(default=None, min_length=1, max_length=300)
    definition_kind: CrsDefinitionKind | None = None
    definition: str | None = Field(default=None, min_length=3, max_length=50000)
    default_axis_order: ProjectedAxisOrder | None = None
    source_reference: str | None = Field(default=None, min_length=3, max_length=5000)
    notes: str | None = Field(default=None, max_length=5000)
    is_active: bool | None = None


class OrganizationCrsDefinitionConfirm(BaseModel):
    confirmed_by: str = Field(min_length=1, max_length=200)
    confirmation_note: str | None = Field(default=None, max_length=5000)


class OrganizationCrsDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_ru: str
    name_kk: str
    name_en: str
    display_name: str
    language: SupportedLanguage

    definition_kind: CrsDefinitionKind
    definition: str
    canonical_wkt: str
    authority_name: str | None
    authority_code: str | None
    default_axis_order: ProjectedAxisOrder
    source_reference: str
    notes: str | None

    is_confirmed: bool
    confirmed_by: str | None
    confirmed_at: datetime | None
    confirmation_note: str | None
    is_active: bool
    selectable: bool

    created_at: datetime
    updated_at: datetime


class OrganizationCrsDefinitionListResponse(BaseModel):
    language: SupportedLanguage
    items: list[OrganizationCrsDefinitionResponse]
