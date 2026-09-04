from pydantic import BaseModel, Field

from app.core.project_info import SupportedLanguage
from app.schemas.coordinates import CoordinateInput, ResolvedCoordinate
from app.schemas.explorer import (
    GeologicalEntityCard,
    IntervalCard,
    RegionHeader,
    SeismicSurveyCard,
    WellCard,
)


class SearchCoordinate(BaseModel):
    latitude: float
    longitude: float
    radius_km: float


class NearbyWellResult(BaseModel):
    distance_m: float
    well: WellCard
    intervals: list[IntervalCard]
    passport_path: str


class NearbyEntityResult(BaseModel):
    distance_m: float
    entity: GeologicalEntityCard


class NearbySeismicResult(BaseModel):
    distance_m: float
    contains_location: bool
    survey: SeismicSurveyCard


class NearbySearchResponse(BaseModel):
    search: SearchCoordinate
    language: SupportedLanguage
    containing_regions: list[RegionHeader]
    nearby_entities: list[NearbyEntityResult]
    nearby_wells: list[NearbyWellResult]
    nearby_seismic_surveys: list[NearbySeismicResult]


class CoordinateNearbySearchRequest(BaseModel):
    coordinate: CoordinateInput
    radius_km: float = Field(default=25.0, gt=0, le=500)
    language: SupportedLanguage = "ru"
    limit: int = Field(default=25, ge=1, le=200)


class CoordinateNearbySearchResponse(BaseModel):
    resolved_coordinate: ResolvedCoordinate
    result: NearbySearchResponse
