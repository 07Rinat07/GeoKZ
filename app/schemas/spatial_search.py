from pydantic import BaseModel

from app.core.project_info import SupportedLanguage
from app.schemas.explorer import GeologicalEntityCard, IntervalCard, RegionHeader, SeismicSurveyCard, WellCard


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
