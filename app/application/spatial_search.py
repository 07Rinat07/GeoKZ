from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.project_info import SupportedLanguage
from app.models.administrative_region import AdministrativeRegion
from app.models.entity import GeologicalEntity
from app.models.subsurface import SeismicSurvey
from app.models.well import Well, WellInterval
from app.schemas.explorer import (
    GeologicalEntityCard,
    IntervalCard,
    RegionHeader,
    SeismicSurveyCard,
    WellCard,
)
from app.schemas.spatial_search import (
    NearbyEntityResult,
    NearbySearchResponse,
    NearbySeismicResult,
    NearbyWellResult,
    SearchCoordinate,
)

_GEOGRAPHY = Geography(srid=4326)
_POINT_GEOGRAPHY = Geography(geometry_type="POINT", srid=4326)


def _localized_name(
    name_ru: str | None,
    name_kk: str | None,
    name_en: str | None,
    language: SupportedLanguage,
) -> str:
    candidates = {
        "ru": (name_ru, name_kk, name_en),
        "kk": (name_kk, name_ru, name_en),
        "en": (name_en, name_ru, name_kk),
    }[language]
    return next((value for value in candidates if value), "")


def _region_card(region: AdministrativeRegion, language: SupportedLanguage) -> RegionHeader:
    return RegionHeader(
        id=region.id,
        external_id=region.external_id,
        level=region.level,
        name_ru=region.name_ru,
        name_kk=region.name_kk,
        name_en=region.name_en,
        display_name=_localized_name(
            region.name_ru,
            region.name_kk,
            region.name_en,
            language,
        ),
        language=language,
    )


def _entity_card(entity: GeologicalEntity, language: SupportedLanguage) -> GeologicalEntityCard:
    return GeologicalEntityCard(
        id=entity.id,
        external_id=entity.external_id,
        object_type=entity.object_type,
        name_ru=entity.name_ru,
        name_kk=entity.name_kk,
        name_en=entity.name_en,
        display_name=_localized_name(
            entity.name_ru,
            entity.name_kk,
            entity.name_en,
            language,
        ),
        verification_status=entity.verification_status,
    )


def _well_card(well: Well, longitude: float | None, latitude: float | None) -> WellCard:
    return WellCard(
        id=well.id,
        external_id=well.external_id,
        name=well.name,
        well_type=well.well_type,
        status=well.status,
        total_depth_m=well.total_depth_m,
        longitude=longitude,
        latitude=latitude,
        object_entity_id=well.object_entity_id,
        verification_status=well.verification_status,
    )


def _interval_card(interval: WellInterval) -> IntervalCard:
    return IntervalCard(
        id=interval.id,
        well_id=interval.well_id,
        external_id=interval.external_id,
        top_depth_m=interval.top_depth_m,
        base_depth_m=interval.base_depth_m,
        local_horizon=interval.local_horizon,
        lithologies=interval.lithologies,
        fluid_type=interval.fluid_type,
        hydrocarbon_status=interval.hydrocarbon_status,
        pressure_mpa=interval.pressure_mpa,
        temperature_c=interval.temperature_c,
        verification_status=interval.verification_status,
    )


def _seismic_card(survey: SeismicSurvey) -> SeismicSurveyCard:
    return SeismicSurveyCard(
        id=survey.id,
        external_id=survey.external_id,
        name=survey.name,
        survey_type=survey.survey_type,
        operator=survey.operator,
        contractor=survey.contractor,
        verification_status=survey.verification_status,
    )


@dataclass(slots=True)
class SpatialSearchService:
    session: AsyncSession

    async def search_nearby(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
        language: SupportedLanguage,
        limit: int,
    ) -> NearbySearchResponse:
        radius_m = radius_km * 1000.0
        point_geometry = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        point_geography = cast(point_geometry, _POINT_GEOGRAPHY)

        containing_regions = list(
            await self.session.scalars(
                select(AdministrativeRegion)
                .where(
                    AdministrativeRegion.geometry.is_not(None),
                    func.ST_Covers(AdministrativeRegion.geometry, point_geometry),
                )
                .order_by(AdministrativeRegion.level, AdministrativeRegion.name_ru)
            )
        )

        entity_distance = func.ST_Distance(
            cast(GeologicalEntity.geometry, _GEOGRAPHY),
            point_geography,
        )
        entity_rows = (
            await self.session.execute(
                select(GeologicalEntity, entity_distance.label("distance_m"))
                .where(
                    GeologicalEntity.geometry.is_not(None),
                    func.ST_DWithin(
                        cast(GeologicalEntity.geometry, _GEOGRAPHY),
                        point_geography,
                        radius_m,
                    ),
                )
                .order_by(entity_distance)
                .limit(limit)
            )
        ).all()

        well_distance = func.ST_Distance(
            cast(Well.location, _POINT_GEOGRAPHY),
            point_geography,
        )
        well_rows = (
            await self.session.execute(
                select(
                    Well,
                    func.ST_X(Well.location).label("longitude"),
                    func.ST_Y(Well.location).label("latitude"),
                    well_distance.label("distance_m"),
                )
                .where(
                    Well.location.is_not(None),
                    func.ST_DWithin(
                        cast(Well.location, _POINT_GEOGRAPHY),
                        point_geography,
                        radius_m,
                    ),
                )
                .order_by(well_distance)
                .limit(limit)
            )
        ).all()

        well_ids: list[UUID] = [well.id for well, _, _, _ in well_rows]
        intervals_by_well: dict[UUID, list[IntervalCard]] = defaultdict(list)
        if well_ids:
            intervals = list(
                await self.session.scalars(
                    select(WellInterval)
                    .where(WellInterval.well_id.in_(well_ids))
                    .order_by(
                        WellInterval.well_id,
                        WellInterval.top_depth_m,
                        WellInterval.base_depth_m,
                    )
                )
            )
            for interval in intervals:
                intervals_by_well[interval.well_id].append(_interval_card(interval))

        seismic_distance = func.ST_Distance(
            cast(SeismicSurvey.coverage, _GEOGRAPHY),
            point_geography,
        )
        seismic_rows = (
            await self.session.execute(
                select(
                    SeismicSurvey,
                    seismic_distance.label("distance_m"),
                    func.ST_Intersects(
                        SeismicSurvey.coverage,
                        point_geometry,
                    ).label("contains_location"),
                )
                .where(
                    SeismicSurvey.coverage.is_not(None),
                    func.ST_DWithin(
                        cast(SeismicSurvey.coverage, _GEOGRAPHY),
                        point_geography,
                        radius_m,
                    ),
                )
                .order_by(seismic_distance)
                .limit(limit)
            )
        ).all()

        return NearbySearchResponse(
            search=SearchCoordinate(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
            ),
            language=language,
            containing_regions=[
                _region_card(region, language) for region in containing_regions
            ],
            nearby_entities=[
                NearbyEntityResult(
                    distance_m=float(distance_m),
                    entity=_entity_card(entity, language),
                )
                for entity, distance_m in entity_rows
            ],
            nearby_wells=[
                NearbyWellResult(
                    distance_m=float(distance_m),
                    well=_well_card(well, well_longitude, well_latitude),
                    intervals=intervals_by_well[well.id],
                    passport_path=f"/api/v1/wells/{well.id}/passport",
                )
                for well, well_longitude, well_latitude, distance_m in well_rows
            ],
            nearby_seismic_surveys=[
                NearbySeismicResult(
                    distance_m=float(distance_m),
                    contains_location=bool(contains_location),
                    survey=_seismic_card(survey),
                )
                for survey, distance_m, contains_location in seismic_rows
            ],
        )
