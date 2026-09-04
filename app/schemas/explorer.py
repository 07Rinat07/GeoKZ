from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.core.project_info import SupportedLanguage
from app.models.enums import (
    ConfidenceLevel,
    FactCategory,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
    WellType,
)


class RegionHeader(BaseModel):
    id: UUID
    external_id: str
    level: str
    name_ru: str
    name_kk: str | None
    name_en: str | None
    display_name: str
    language: SupportedLanguage


class GeologicalEntityCard(BaseModel):
    id: UUID
    external_id: str
    object_type: str
    name_ru: str
    name_kk: str | None
    name_en: str | None
    display_name: str
    verification_status: VerificationStatus


class WellCard(BaseModel):
    id: UUID
    external_id: str
    name: str
    well_type: WellType
    status: str | None
    total_depth_m: Decimal | None
    longitude: float | None
    latitude: float | None
    object_entity_id: UUID | None
    verification_status: VerificationStatus


class SeismicSurveyCard(BaseModel):
    id: UUID
    external_id: str
    name: str
    survey_type: str
    operator: str | None
    contractor: str | None
    verification_status: VerificationStatus


class FactCard(BaseModel):
    id: UUID
    external_id: str
    category: FactCategory
    normalized_statement: str
    confidence: ConfidenceLevel
    primary_source_id: UUID
    verification_status: VerificationStatus


class IntervalCard(BaseModel):
    id: UUID
    well_id: UUID
    external_id: str
    top_depth_m: Decimal
    base_depth_m: Decimal
    local_horizon: str | None
    lithologies: list[str]
    fluid_type: FluidType
    hydrocarbon_status: HydrocarbonStatus
    pressure_mpa: Decimal | None
    temperature_c: Decimal | None
    verification_status: VerificationStatus


class TerritoryOverviewResponse(BaseModel):
    region: RegionHeader
    entities: list[GeologicalEntityCard]
    wells: list[WellCard]
    seismic_surveys: list[SeismicSurveyCard]


class GeologicalEntityPassportResponse(BaseModel):
    entity: GeologicalEntityCard
    administrative_regions: list[RegionHeader]
    facts: list[FactCard]
    wells: list[WellCard]
    intervals: list[IntervalCard]
    seismic_surveys: list[SeismicSurveyCard]
