from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import ResourceNotFoundError
from app.core.project_info import SupportedLanguage
from app.models.administrative_region import AdministrativeRegion
from app.models.entity import (
    GeologicalEntity,
    geological_entity_administrative_regions,
)
from app.models.fact import Fact
from app.models.subsurface import SeismicSurvey
from app.models.well import Well, WellInterval
from app.schemas.explorer import (
    FactCard,
    GeologicalEntityCard,
    GeologicalEntityPassportResponse,
    IntervalCard,
    RegionHeader,
    SeismicSurveyCard,
    TerritoryOverviewResponse,
    WellCard,
)


def _localized_name(
    *,
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


def _region_header(
    region: AdministrativeRegion,
    language: SupportedLanguage,
) -> RegionHeader:
    return RegionHeader(
        id=region.id,
        external_id=region.external_id,
        level=region.level,
        name_ru=region.name_ru,
        name_kk=region.name_kk,
        name_en=region.name_en,
        display_name=_localized_name(
            name_ru=region.name_ru,
            name_kk=region.name_kk,
            name_en=region.name_en,
            language=language,
        ),
        language=language,
    )


def _entity_card(
    entity: GeologicalEntity,
    language: SupportedLanguage,
) -> GeologicalEntityCard:
    return GeologicalEntityCard(
        id=entity.id,
        external_id=entity.external_id,
        object_type=entity.object_type,
        name_ru=entity.name_ru,
        name_kk=entity.name_kk,
        name_en=entity.name_en,
        display_name=_localized_name(
            name_ru=entity.name_ru,
            name_kk=entity.name_kk,
            name_en=entity.name_en,
            language=language,
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
class TerritoryExplorerService:
    session: AsyncSession

    async def get_overview(
        self,
        region_id: UUID,
        language: SupportedLanguage,
    ) -> TerritoryOverviewResponse:
        region = await self.session.get(AdministrativeRegion, region_id)
        if region is None:
            raise ResourceNotFoundError("Административный регион не найден")

        entities = list(
            await self.session.scalars(
                select(GeologicalEntity)
                .join(
                    geological_entity_administrative_regions,
                    GeologicalEntity.id
                    == geological_entity_administrative_regions.c.entity_id,
                )
                .where(
                    geological_entity_administrative_regions.c.administrative_region_id
                    == region_id
                )
                .order_by(GeologicalEntity.object_type, GeologicalEntity.name_ru)
            )
        )

        well_rows: list[tuple[Well, float | None, float | None]] = []
        seismic_surveys: list[SeismicSurvey] = []
        if region.geometry is not None:
            well_rows = [
                (well, longitude, latitude)
                for well, longitude, latitude in (
                    await self.session.execute(
                        select(
                            Well,
                            func.ST_X(Well.location),
                            func.ST_Y(Well.location),
                        )
                        .where(
                            Well.location.is_not(None),
                            func.ST_Within(Well.location, region.geometry),
                        )
                        .order_by(Well.name)
                    )
                ).all()
            ]
            seismic_surveys = list(
                await self.session.scalars(
                    select(SeismicSurvey)
                    .where(
                        SeismicSurvey.coverage.is_not(None),
                        func.ST_Intersects(SeismicSurvey.coverage, region.geometry),
                    )
                    .order_by(SeismicSurvey.name)
                )
            )

        return TerritoryOverviewResponse(
            region=_region_header(region, language),
            entities=[_entity_card(entity, language) for entity in entities],
            wells=[_well_card(well, longitude, latitude) for well, longitude, latitude in well_rows],
            seismic_surveys=[_seismic_card(survey) for survey in seismic_surveys],
        )


@dataclass(slots=True)
class GeologicalEntityPassportService:
    session: AsyncSession

    async def get_passport(
        self,
        entity_id: UUID,
        language: SupportedLanguage,
    ) -> GeologicalEntityPassportResponse:
        entity = await self.session.get(GeologicalEntity, entity_id)
        if entity is None:
            raise ResourceNotFoundError("Геологический объект не найден")

        regions = list(
            await self.session.scalars(
                select(AdministrativeRegion)
                .join(
                    geological_entity_administrative_regions,
                    AdministrativeRegion.id
                    == geological_entity_administrative_regions.c.administrative_region_id,
                )
                .where(geological_entity_administrative_regions.c.entity_id == entity_id)
                .order_by(AdministrativeRegion.level, AdministrativeRegion.name_ru)
            )
        )

        facts = list(
            await self.session.scalars(
                select(Fact)
                .where(Fact.entity_id == entity_id)
                .order_by(Fact.category, Fact.created_at)
            )
        )

        well_rows = [
            (well, longitude, latitude)
            for well, longitude, latitude in (
                await self.session.execute(
                    select(
                        Well,
                        func.ST_X(Well.location),
                        func.ST_Y(Well.location),
                    )
                    .where(
                        or_(
                            Well.object_entity_id == entity_id,
                            Well.entity_id == entity_id,
                        )
                    )
                    .order_by(Well.name)
                )
            ).all()
        ]
        well_ids = [well.id for well, _, _ in well_rows]
        intervals = (
            list(
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
            if well_ids
            else []
        )

        seismic_surveys: list[SeismicSurvey] = []
        if entity.geometry is not None:
            seismic_surveys = list(
                await self.session.scalars(
                    select(SeismicSurvey)
                    .where(
                        SeismicSurvey.coverage.is_not(None),
                        func.ST_Intersects(SeismicSurvey.coverage, entity.geometry),
                    )
                    .order_by(SeismicSurvey.name)
                )
            )

        return GeologicalEntityPassportResponse(
            entity=_entity_card(entity, language),
            administrative_regions=[_region_header(region, language) for region in regions],
            facts=[
                FactCard(
                    id=fact.id,
                    external_id=fact.external_id,
                    category=fact.category,
                    normalized_statement=fact.normalized_statement,
                    confidence=fact.confidence,
                    primary_source_id=fact.primary_source_id,
                    verification_status=fact.verification_status,
                )
                for fact in facts
            ],
            wells=[_well_card(well, longitude, latitude) for well, longitude, latitude in well_rows],
            intervals=[
                IntervalCard(
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
                for interval in intervals
            ],
            seismic_surveys=[_seismic_card(survey) for survey in seismic_surveys],
        )
