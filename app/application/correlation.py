from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.application.errors import ResourceNotFoundError
from app.core.project_info import SupportedLanguage
from app.models.correlation import WellMarker
from app.models.enums import DepthReference, VerificationStatus
from app.models.well import Well, WellInterval
from app.schemas.correlation import (
    CorrelationInterval,
    CorrelationMarker,
    CorrelationWellColumn,
    MarkerDifference,
    ReservoirDifference,
    WellCorrelationResponse,
)
from app.schemas.explorer import WellCard

_POINT_GEOGRAPHY = Geography(geometry_type="POINT", srid=4326)
_STATUS_RANK = {
    VerificationStatus.VERIFIED: 0,
    VerificationStatus.REVIEWED: 1,
    VerificationStatus.DRAFT: 2,
    VerificationStatus.CONFLICT: 3,
    VerificationStatus.OBSOLETE: 4,
    VerificationStatus.REJECTED: 5,
}


def _localized_marker_name(marker: WellMarker, language: SupportedLanguage) -> str:
    values = {
        "ru": (marker.name_ru, marker.name_kk, marker.name_en),
        "kk": (marker.name_kk, marker.name_ru, marker.name_en),
        "en": (marker.name_en, marker.name_ru, marker.name_kk),
    }[language]
    return next((value for value in values if value), marker.marker_code)


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


def _marker_schema(marker: WellMarker, language: SupportedLanguage) -> CorrelationMarker:
    return CorrelationMarker(
        id=marker.id,
        marker_code=marker.marker_code,
        marker_type=marker.marker_type,
        display_name=_localized_marker_name(marker, language),
        depth_m=marker.depth_m,
        depth_reference=marker.depth_reference,
        measured_depth_m=marker.measured_depth_m,
        true_vertical_depth_m=marker.true_vertical_depth_m,
        tvdss_m=marker.tvdss_m,
        confidence_percent=marker.confidence_percent,
        verification_status=marker.verification_status,
    )


def _interval_schema(interval: WellInterval) -> CorrelationInterval:
    return CorrelationInterval(
        id=interval.id,
        external_id=interval.external_id,
        top_depth_m=interval.top_depth_m,
        base_depth_m=interval.base_depth_m,
        depth_reference=interval.depth_reference,
        local_horizon=interval.local_horizon,
        lithologies=interval.lithologies,
        porosity_percent=interval.porosity_percent,
        permeability_md=interval.permeability_md,
        net_pay_m=interval.net_pay_m,
        fluid_type=interval.fluid_type,
        hydrocarbon_status=interval.hydrocarbon_status,
        verification_status=interval.verification_status,
    )


def _preferred_marker(markers: list[WellMarker]) -> WellMarker:
    return sorted(
        markers,
        key=lambda marker: (
            _STATUS_RANK.get(marker.verification_status, 99),
            -(
                float(marker.confidence_percent)
                if marker.confidence_percent is not None
                else -1.0
            ),
        ),
    )[0]


def _preferred_interval(intervals: list[WellInterval]) -> WellInterval:
    return sorted(
        intervals,
        key=lambda interval: (
            _STATUS_RANK.get(interval.verification_status, 99),
            -(
                float(interval.net_pay_m)
                if interval.net_pay_m is not None
                else -1.0
            ),
        ),
    )[0]


def _comparison_depth(marker: WellMarker) -> tuple[DepthReference, Decimal] | None:
    if marker.tvdss_m is not None:
        return DepthReference.TVDSS, marker.tvdss_m
    if marker.true_vertical_depth_m is not None:
        return DepthReference.TVD, marker.true_vertical_depth_m
    if marker.measured_depth_m is not None:
        return DepthReference.MD, marker.measured_depth_m
    if marker.depth_reference != DepthReference.UNKNOWN:
        return marker.depth_reference, marker.depth_m
    return None


def _normalize_horizon(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.casefold().split())
    return normalized or None


def _not_comparable_reason(language: SupportedLanguage) -> str:
    return {
        "ru": "Нет общей сопоставимой системы глубин для этого репера.",
        "kk": "Бұл репер үшін ортақ салыстырылатын тереңдік жүйесі жоқ.",
        "en": "No common comparable depth reference is available for this marker.",
    }[language]


def _interval_not_comparable_reason(language: SupportedLanguage) -> str:
    return {
        "ru": "Интервалы имеют разные или неизвестные системы глубин; мощность не сравнивается автоматически.",
        "kk": "Интервалдардың тереңдік жүйелері әртүрлі немесе белгісіз; қалыңдық автоматты түрде салыстырылмайды.",
        "en": "Intervals use different or unknown depth references; thickness is not compared automatically.",
    }[language]


def _comparison_note(language: SupportedLanguage) -> str:
    return {
        "ru": (
            "Корреляция является рабочим сравнением. Для реперов предпочтительно TVDSS; при его отсутствии "
            "используется совместимая TVD или MD. Интервалы сравниваются только в общей системе глубин. "
            "Результат не заменяет экспертную геологическую интерпретацию."
        ),
        "kk": (
            "Корреляция жұмыс салыстыруы болып табылады. Реперлер үшін TVDSS басым; ол болмаған кезде "
            "үйлесімді TVD немесе MD қолданылады. Интервалдар тек ортақ тереңдік жүйесінде салыстырылады. "
            "Нәтиже сараптамалық геологиялық интерпретацияны алмастырмайды."
        ),
        "en": (
            "Correlation is a working comparison. TVDSS is preferred for markers; compatible TVD or MD is "
            "used when unavailable. Intervals are compared only in a common depth reference. The result does "
            "not replace expert geological interpretation."
        ),
    }[language]


@dataclass(slots=True)
class WellCorrelationService:
    session: AsyncSession

    async def compare(
        self,
        *,
        reference_well_id: UUID,
        well_ids: list[UUID],
        language: SupportedLanguage,
    ) -> WellCorrelationResponse:
        ordered_ids = list(dict.fromkeys([reference_well_id, *well_ids]))

        well_rows = (
            await self.session.execute(
                select(
                    Well,
                    func.ST_X(Well.location).label("longitude"),
                    func.ST_Y(Well.location).label("latitude"),
                ).where(Well.id.in_(ordered_ids))
            )
        ).all()
        wells_by_id = {
            well.id: (well, longitude, latitude)
            for well, longitude, latitude in well_rows
        }

        if reference_well_id not in wells_by_id:
            raise ResourceNotFoundError("Опорная скважина не найдена")

        missing_ids = [
            well_id for well_id in ordered_ids if well_id not in wells_by_id
        ]
        if missing_ids:
            raise ResourceNotFoundError(
                f"Скважины не найдены: {', '.join(map(str, missing_ids))}"
            )

        markers = list(
            await self.session.scalars(
                select(WellMarker)
                .where(WellMarker.well_id.in_(ordered_ids))
                .order_by(
                    WellMarker.well_id,
                    WellMarker.marker_code,
                    WellMarker.depth_m,
                )
            )
        )
        markers_by_well: dict[UUID, list[WellMarker]] = defaultdict(list)
        markers_by_well_and_code: dict[
            UUID, dict[str, list[WellMarker]]
        ] = defaultdict(lambda: defaultdict(list))
        for marker in markers:
            markers_by_well[marker.well_id].append(marker)
            markers_by_well_and_code[marker.well_id][marker.marker_code].append(
                marker
            )

        intervals = list(
            await self.session.scalars(
                select(WellInterval)
                .where(WellInterval.well_id.in_(ordered_ids))
                .order_by(
                    WellInterval.well_id,
                    WellInterval.top_depth_m,
                    WellInterval.base_depth_m,
                )
            )
        )
        intervals_by_well: dict[UUID, list[WellInterval]] = defaultdict(list)
        intervals_by_well_and_horizon: dict[
            UUID, dict[str, list[WellInterval]]
        ] = defaultdict(lambda: defaultdict(list))
        for interval in intervals:
            intervals_by_well[interval.well_id].append(interval)
            horizon_key = _normalize_horizon(interval.local_horizon)
            if horizon_key is not None:
                intervals_by_well_and_horizon[interval.well_id][horizon_key].append(
                    interval
                )

        distance_by_well = await self._distances(reference_well_id, ordered_ids)

        columns = [
            CorrelationWellColumn(
                well=_well_card(*wells_by_id[well_id]),
                distance_from_reference_m=distance_by_well.get(well_id),
                markers=[
                    _marker_schema(marker, language)
                    for marker in markers_by_well[well_id]
                ],
                intervals=[
                    _interval_schema(interval)
                    for interval in intervals_by_well[well_id]
                ],
            )
            for well_id in ordered_ids
        ]

        compared_ids = [
            well_id for well_id in ordered_ids if well_id != reference_well_id
        ]
        marker_differences = self._build_marker_differences(
            reference_well_id=reference_well_id,
            compared_well_ids=compared_ids,
            markers_by_well_and_code=markers_by_well_and_code,
            language=language,
        )
        reservoir_differences = self._build_reservoir_differences(
            reference_well_id=reference_well_id,
            compared_well_ids=compared_ids,
            intervals_by_well_and_horizon=intervals_by_well_and_horizon,
            language=language,
        )

        return WellCorrelationResponse(
            language=language,
            reference_well_id=reference_well_id,
            columns=columns,
            marker_differences=marker_differences,
            reservoir_differences=reservoir_differences,
            comparison_note=_comparison_note(language),
        )

    async def _distances(
        self,
        reference_well_id: UUID,
        well_ids: list[UUID],
    ) -> dict[UUID, float | None]:
        reference = aliased(Well)
        candidate = aliased(Well)
        reference_location = (
            select(reference.location)
            .where(reference.id == reference_well_id)
            .scalar_subquery()
        )
        distance = func.ST_Distance(
            cast(candidate.location, _POINT_GEOGRAPHY),
            cast(reference_location, _POINT_GEOGRAPHY),
        )
        rows = (
            await self.session.execute(
                select(candidate.id, distance.label("distance_m")).where(
                    candidate.id.in_(well_ids),
                    candidate.location.is_not(None),
                    reference_location.is_not(None),
                )
            )
        ).all()
        result: dict[UUID, float | None] = {
            well_id: None for well_id in well_ids
        }
        result[reference_well_id] = 0.0
        for well_id, distance_m in rows:
            result[well_id] = float(distance_m)
        return result

    def _build_marker_differences(
        self,
        *,
        reference_well_id: UUID,
        compared_well_ids: list[UUID],
        markers_by_well_and_code: dict[UUID, dict[str, list[WellMarker]]],
        language: SupportedLanguage,
    ) -> list[MarkerDifference]:
        result: list[MarkerDifference] = []
        reference_markers = markers_by_well_and_code[reference_well_id]

        for marker_code, reference_candidates in reference_markers.items():
            reference_marker = _preferred_marker(reference_candidates)
            reference_depth = _comparison_depth(reference_marker)

            for compared_well_id in compared_well_ids:
                compared_candidates = markers_by_well_and_code[
                    compared_well_id
                ].get(marker_code)
                if not compared_candidates:
                    continue
                compared_marker = _preferred_marker(compared_candidates)
                compared_depth = _comparison_depth(compared_marker)

                if (
                    reference_depth is not None
                    and compared_depth is not None
                    and reference_depth[0] == compared_depth[0]
                ):
                    reference_value = reference_depth[1]
                    compared_value = compared_depth[1]
                    result.append(
                        MarkerDifference(
                            marker_code=marker_code,
                            compared_well_id=compared_well_id,
                            reference_depth_m=reference_value,
                            compared_depth_m=compared_value,
                            depth_reference=reference_depth[0],
                            delta_m=compared_value - reference_value,
                            comparable=True,
                        )
                    )
                else:
                    result.append(
                        MarkerDifference(
                            marker_code=marker_code,
                            compared_well_id=compared_well_id,
                            reference_depth_m=(
                                reference_depth[1] if reference_depth else None
                            ),
                            compared_depth_m=(
                                compared_depth[1] if compared_depth else None
                            ),
                            depth_reference=None,
                            delta_m=None,
                            comparable=False,
                            reason=_not_comparable_reason(language),
                        )
                    )

        return result

    def _build_reservoir_differences(
        self,
        *,
        reference_well_id: UUID,
        compared_well_ids: list[UUID],
        intervals_by_well_and_horizon: dict[
            UUID, dict[str, list[WellInterval]]
        ],
        language: SupportedLanguage,
    ) -> list[ReservoirDifference]:
        result: list[ReservoirDifference] = []
        reference_horizons = intervals_by_well_and_horizon[reference_well_id]

        for horizon_key, reference_candidates in reference_horizons.items():
            reference_interval = _preferred_interval(reference_candidates)
            reference_thickness = (
                reference_interval.base_depth_m - reference_interval.top_depth_m
            )

            for compared_well_id in compared_well_ids:
                compared_candidates = intervals_by_well_and_horizon[
                    compared_well_id
                ].get(horizon_key)
                if not compared_candidates:
                    continue
                compared_interval = _preferred_interval(compared_candidates)
                compared_thickness = (
                    compared_interval.base_depth_m - compared_interval.top_depth_m
                )
                comparable = (
                    reference_interval.depth_reference != DepthReference.UNKNOWN
                    and reference_interval.depth_reference
                    == compared_interval.depth_reference
                )

                net_pay_delta = None
                if (
                    reference_interval.net_pay_m is not None
                    and compared_interval.net_pay_m is not None
                ):
                    net_pay_delta = (
                        compared_interval.net_pay_m - reference_interval.net_pay_m
                    )

                result.append(
                    ReservoirDifference(
                        horizon=reference_interval.local_horizon or horizon_key,
                        compared_well_id=compared_well_id,
                        reference_interval_id=reference_interval.id,
                        compared_interval_id=compared_interval.id,
                        depth_reference=(
                            reference_interval.depth_reference if comparable else None
                        ),
                        reference_thickness_m=reference_thickness,
                        compared_thickness_m=compared_thickness,
                        thickness_delta_m=(
                            compared_thickness - reference_thickness
                            if comparable
                            else None
                        ),
                        reference_net_pay_m=reference_interval.net_pay_m,
                        compared_net_pay_m=compared_interval.net_pay_m,
                        net_pay_delta_m=net_pay_delta,
                        reference_porosity_percent=(
                            reference_interval.porosity_percent
                        ),
                        compared_porosity_percent=(
                            compared_interval.porosity_percent
                        ),
                        reference_permeability_md=(
                            reference_interval.permeability_md
                        ),
                        compared_permeability_md=(
                            compared_interval.permeability_md
                        ),
                        reference_lithologies=reference_interval.lithologies,
                        compared_lithologies=compared_interval.lithologies,
                        lithology_changed=(
                            set(map(str.casefold, reference_interval.lithologies))
                            != set(
                                map(str.casefold, compared_interval.lithologies)
                            )
                        ),
                        reference_fluid_type=reference_interval.fluid_type,
                        compared_fluid_type=compared_interval.fluid_type,
                        fluid_changed=(
                            reference_interval.fluid_type
                            != compared_interval.fluid_type
                        ),
                        reference_hydrocarbon_status=(
                            reference_interval.hydrocarbon_status
                        ),
                        compared_hydrocarbon_status=(
                            compared_interval.hydrocarbon_status
                        ),
                        hydrocarbon_status_changed=(
                            reference_interval.hydrocarbon_status
                            != compared_interval.hydrocarbon_status
                        ),
                        comparable_thickness=comparable,
                        reason=(
                            None
                            if comparable
                            else _interval_not_comparable_reason(language)
                        ),
                    )
                )

        return result
