from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.correlation import WellCorrelationService
from app.core.project_info import SupportedLanguage
from app.models.enums import DepthReference
from app.schemas.correlation import (
    CorrelationInterval,
    CorrelationMarker,
    CrossSectionCorrelationLine,
    CrossSectionDepthAxis,
    CrossSectionIntervalView,
    CrossSectionLineKind,
    CrossSectionMarkerView,
    CrossSectionWarning,
    CrossSectionWarningCode,
    CrossSectionWellColumnView,
    WellCorrelationResponse,
    WellCrossSectionViewResponse,
)

_DEPTH_PRIORITY = (
    DepthReference.TVDSS,
    DepthReference.TVD,
    DepthReference.MD,
)


def _title(language: SupportedLanguage) -> str:
    return {
        "ru": "Корреляционный разрез скважин",
        "kk": "Ұңғымалардың корреляциялық қимасы",
        "en": "Well correlation cross-section",
    }[language]


def _policy_note(language: SupportedLanguage) -> str:
    return {
        "ru": (
            "Разрез является визуальным представлением уже рассчитанной корреляции. "
            "GeoKZ предпочитает TVDSS, затем совместимую TVD и MD. Элементы в другой "
            "системе глубин не переносятся на выбранную шкалу автоматически."
        ),
        "kk": (
            "Қима алдын ала есептелген корреляцияның визуалды көрінісі болып табылады. "
            "GeoKZ алдымен TVDSS, кейін үйлесімді TVD және MD қолданады. Басқа тереңдік "
            "жүйесіндегі элементтер таңдалған шкалаға автоматты түрде көшірілмейді."
        ),
        "en": (
            "The section is a visual representation of an already computed correlation. "
            "GeoKZ prefers TVDSS, then compatible TVD and MD. Data in a different depth "
            "reference is not silently projected onto the selected scale."
        ),
    }[language]


def _warning_message(
    code: CrossSectionWarningCode,
    language: SupportedLanguage,
    *,
    count: int | None = None,
) -> str:
    messages = {
        CrossSectionWarningCode.DEPTH_REFERENCE_MISMATCH: {
            "ru": "Часть данных скважины использует другую систему глубин и скрыта со шкалы разреза.",
            "kk": "Ұңғыма деректерінің бір бөлігі басқа тереңдік жүйесін қолданады және қима шкаласында көрсетілмейді.",
            "en": "Some well data uses a different depth reference and is not rendered on the section scale.",
        },
        CrossSectionWarningCode.NON_COMPARABLE_MARKERS: {
            "ru": f"Несопоставимых пар реперов: {count or 0}. Линии для них не строятся.",
            "kk": f"Салыстырылмайтын репер жұптары: {count or 0}. Олар үшін сызық салынбайды.",
            "en": f"Non-comparable marker pairs: {count or 0}. No lines are drawn for them.",
        },
        CrossSectionWarningCode.NON_COMPARABLE_INTERVALS: {
            "ru": f"Несопоставимых пар интервалов: {count or 0}. Линии горизонтов для них не строятся.",
            "kk": f"Салыстырылмайтын интервал жұптары: {count or 0}. Олар үшін горизонт сызықтары салынбайды.",
            "en": f"Non-comparable interval pairs: {count or 0}. No horizon lines are drawn for them.",
        },
        CrossSectionWarningCode.NO_RENDERABLE_DATA: {
            "ru": "Для выбранных скважин нет данных, которые можно безопасно отобразить в общей системе глубин.",
            "kk": "Таңдалған ұңғымалар үшін ортақ тереңдік жүйесінде қауіпсіз көрсетуге болатын деректер жоқ.",
            "en": "The selected wells have no data that can be safely rendered in a common depth reference.",
        },
        CrossSectionWarningCode.NO_CORRELATION_LINES: {
            "ru": "Нет подтверждённых сопоставимых реперов или интервалов для построения корреляционных линий.",
            "kk": "Корреляциялық сызықтарды салу үшін расталған салыстырылатын реперлер немесе интервалдар жоқ.",
            "en": "No comparable marker or interval pairs are available for correlation lines.",
        },
    }
    return messages[code][language]


def _marker_depth(
    marker: CorrelationMarker,
    depth_reference: DepthReference,
) -> Decimal | None:
    if depth_reference == DepthReference.TVDSS:
        if marker.tvdss_m is not None:
            return marker.tvdss_m
    elif depth_reference == DepthReference.TVD:
        if marker.true_vertical_depth_m is not None:
            return marker.true_vertical_depth_m
    elif depth_reference == DepthReference.MD:
        if marker.measured_depth_m is not None:
            return marker.measured_depth_m

    if marker.depth_reference == depth_reference:
        return marker.depth_m
    return None


def _select_depth_reference(correlation: WellCorrelationResponse) -> DepthReference:
    comparable_references = {
        difference.depth_reference
        for difference in correlation.marker_differences
        if difference.comparable and difference.depth_reference is not None
    }
    comparable_references.update(
        difference.depth_reference
        for difference in correlation.reservoir_differences
        if difference.comparable_thickness and difference.depth_reference is not None
    )
    for depth_reference in _DEPTH_PRIORITY:
        if depth_reference in comparable_references:
            return depth_reference

    available_references: set[DepthReference] = set()
    for column in correlation.columns:
        for marker in column.markers:
            for depth_reference in _DEPTH_PRIORITY:
                if _marker_depth(marker, depth_reference) is not None:
                    available_references.add(depth_reference)
        for interval in column.intervals:
            if interval.depth_reference != DepthReference.UNKNOWN:
                available_references.add(interval.depth_reference)

    for depth_reference in _DEPTH_PRIORITY:
        if depth_reference in available_references:
            return depth_reference
    return DepthReference.TVDSS


def _axis(values: list[Decimal], depth_reference: DepthReference) -> CrossSectionDepthAxis:
    if not values:
        return CrossSectionDepthAxis(
            depth_reference=depth_reference,
            min_depth_m=Decimal("0"),
            max_depth_m=Decimal("1"),
            padding_m=Decimal("0"),
        )

    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum
    padding = max(Decimal("10"), span * Decimal("0.05")) if span else Decimal("10")
    return CrossSectionDepthAxis(
        depth_reference=depth_reference,
        min_depth_m=minimum - padding,
        max_depth_m=maximum + padding,
        padding_m=padding,
    )


def build_cross_section_view(
    correlation: WellCorrelationResponse,
) -> WellCrossSectionViewResponse:
    depth_reference = _select_depth_reference(correlation)
    depth_values: list[Decimal] = []
    warnings: list[CrossSectionWarning] = []
    columns: list[CrossSectionWellColumnView] = []
    interval_lookup: dict[UUID, tuple[int, UUID, CrossSectionIntervalView]] = {}
    column_index_by_well: dict[UUID, int] = {}

    for column_index, source_column in enumerate(correlation.columns):
        column_index_by_well[source_column.well.id] = column_index
        marker_views: list[CrossSectionMarkerView] = []
        interval_views: list[CrossSectionIntervalView] = []
        mismatch_count = 0

        for marker in source_column.markers:
            render_depth = _marker_depth(marker, depth_reference)
            renderable = render_depth is not None
            if renderable:
                depth_values.append(render_depth)
            else:
                mismatch_count += 1
            marker_views.append(
                CrossSectionMarkerView(
                    marker_id=marker.id,
                    marker_code=marker.marker_code,
                    display_name=marker.display_name,
                    marker_type=marker.marker_type,
                    depth_m=render_depth,
                    depth_reference=depth_reference,
                    renderable=renderable,
                    confidence_percent=marker.confidence_percent,
                    verification_status=marker.verification_status,
                )
            )

        for interval in source_column.intervals:
            renderable = interval.depth_reference == depth_reference
            top_depth = interval.top_depth_m if renderable else None
            base_depth = interval.base_depth_m if renderable else None
            if renderable:
                depth_values.extend((interval.top_depth_m, interval.base_depth_m))
            else:
                mismatch_count += 1
            view = CrossSectionIntervalView(
                interval_id=interval.id,
                external_id=interval.external_id,
                horizon=interval.local_horizon,
                top_depth_m=top_depth,
                base_depth_m=base_depth,
                depth_reference=interval.depth_reference,
                renderable=renderable,
                lithologies=interval.lithologies,
                fluid_type=interval.fluid_type,
                hydrocarbon_status=interval.hydrocarbon_status,
                net_pay_m=interval.net_pay_m,
                verification_status=interval.verification_status,
            )
            interval_views.append(view)
            interval_lookup[interval.id] = (
                column_index,
                source_column.well.id,
                view,
            )

        if mismatch_count:
            warnings.append(
                CrossSectionWarning(
                    code=CrossSectionWarningCode.DEPTH_REFERENCE_MISMATCH,
                    message=_warning_message(
                        CrossSectionWarningCode.DEPTH_REFERENCE_MISMATCH,
                        correlation.language,
                    ),
                    well_id=source_column.well.id,
                )
            )

        columns.append(
            CrossSectionWellColumnView(
                column_index=column_index,
                well=source_column.well,
                is_reference=source_column.well.id == correlation.reference_well_id,
                distance_from_reference_m=source_column.distance_from_reference_m,
                markers=marker_views,
                intervals=interval_views,
            )
        )

    lines: list[CrossSectionCorrelationLine] = []

    for difference in correlation.marker_differences:
        if (
            not difference.comparable
            or difference.depth_reference != depth_reference
            or difference.reference_depth_m is None
            or difference.compared_depth_m is None
        ):
            continue
        compared_column_index = column_index_by_well.get(difference.compared_well_id)
        reference_column_index = column_index_by_well.get(correlation.reference_well_id)
        if compared_column_index is None or reference_column_index is None:
            continue
        lines.append(
            CrossSectionCorrelationLine(
                kind=CrossSectionLineKind.MARKER,
                key=difference.marker_code,
                depth_reference=depth_reference,
                from_column_index=reference_column_index,
                to_column_index=compared_column_index,
                from_well_id=correlation.reference_well_id,
                to_well_id=difference.compared_well_id,
                from_depth_m=difference.reference_depth_m,
                to_depth_m=difference.compared_depth_m,
            )
        )

    for difference in correlation.reservoir_differences:
        if (
            not difference.comparable_thickness
            or difference.depth_reference != depth_reference
        ):
            continue
        reference_entry = interval_lookup.get(difference.reference_interval_id)
        compared_entry = interval_lookup.get(difference.compared_interval_id)
        if reference_entry is None or compared_entry is None:
            continue
        reference_column_index, reference_well_id, reference_interval = reference_entry
        compared_column_index, compared_well_id, compared_interval = compared_entry
        if (
            not reference_interval.renderable
            or not compared_interval.renderable
            or reference_interval.top_depth_m is None
            or reference_interval.base_depth_m is None
            or compared_interval.top_depth_m is None
            or compared_interval.base_depth_m is None
        ):
            continue
        lines.append(
            CrossSectionCorrelationLine(
                kind=CrossSectionLineKind.HORIZON,
                key=difference.horizon,
                depth_reference=depth_reference,
                from_column_index=reference_column_index,
                to_column_index=compared_column_index,
                from_well_id=reference_well_id,
                to_well_id=compared_well_id,
                from_depth_m=(
                    reference_interval.top_depth_m + reference_interval.base_depth_m
                )
                / Decimal("2"),
                to_depth_m=(
                    compared_interval.top_depth_m + compared_interval.base_depth_m
                )
                / Decimal("2"),
            )
        )

    non_comparable_markers = sum(
        not difference.comparable for difference in correlation.marker_differences
    )
    if non_comparable_markers:
        warnings.append(
            CrossSectionWarning(
                code=CrossSectionWarningCode.NON_COMPARABLE_MARKERS,
                message=_warning_message(
                    CrossSectionWarningCode.NON_COMPARABLE_MARKERS,
                    correlation.language,
                    count=non_comparable_markers,
                ),
            )
        )

    non_comparable_intervals = sum(
        not difference.comparable_thickness
        for difference in correlation.reservoir_differences
    )
    if non_comparable_intervals:
        warnings.append(
            CrossSectionWarning(
                code=CrossSectionWarningCode.NON_COMPARABLE_INTERVALS,
                message=_warning_message(
                    CrossSectionWarningCode.NON_COMPARABLE_INTERVALS,
                    correlation.language,
                    count=non_comparable_intervals,
                ),
            )
        )

    has_renderable_data = bool(depth_values)
    if not has_renderable_data:
        warnings.append(
            CrossSectionWarning(
                code=CrossSectionWarningCode.NO_RENDERABLE_DATA,
                message=_warning_message(
                    CrossSectionWarningCode.NO_RENDERABLE_DATA,
                    correlation.language,
                ),
            )
        )
    if not lines:
        warnings.append(
            CrossSectionWarning(
                code=CrossSectionWarningCode.NO_CORRELATION_LINES,
                message=_warning_message(
                    CrossSectionWarningCode.NO_CORRELATION_LINES,
                    correlation.language,
                ),
            )
        )

    return WellCrossSectionViewResponse(
        language=correlation.language,
        reference_well_id=correlation.reference_well_id,
        title=_title(correlation.language),
        policy_note=_policy_note(correlation.language),
        depth_axis=_axis(depth_values, depth_reference),
        columns=columns,
        correlation_lines=lines,
        warnings=warnings,
        has_renderable_data=has_renderable_data,
    )


@dataclass(slots=True)
class WellCrossSectionViewService:
    session: AsyncSession

    async def build(
        self,
        *,
        reference_well_id: UUID,
        well_ids: list[UUID],
        language: SupportedLanguage,
    ) -> WellCrossSectionViewResponse:
        correlation = await WellCorrelationService(self.session).compare(
            reference_well_id=reference_well_id,
            well_ids=well_ids,
            language=language,
        )
        return build_cross_section_view(correlation)
