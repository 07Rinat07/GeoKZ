from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.coordinate_resolution import CoordinateResolutionService
from app.application.correlation_view import WellCrossSectionViewService
from app.application.errors import DemoCorrelationSelectionError
from app.application.spatial_search import SpatialSearchService
from app.core.demo_data import DEMO_CORRELATION_DATASET, DEMO_CORRELATION_WELL_PREFIX
from app.core.project_info import SupportedLanguage
from app.models.well import Well
from app.schemas.demo_correlation import (
    DemoCorrelationSelection,
    DemoCorrelationSelectionContract,
    DemoCorrelationWellOption,
    DemoCorrelationWorkflowRequest,
    DemoCorrelationWorkflowResponse,
    DemoCorrelationWorkflowStage,
)


def _synthetic_warning(language: SupportedLanguage) -> str:
    return {
        "ru": (
            "Это только синтетический демонстрационный набор GeoKZ. "
            "Его нельзя использовать как производственные геологические факты."
        ),
        "kk": (
            "Бұл тек GeoKZ синтетикалық демонстрациялық деректер жиыны. "
            "Оны өндірістік геологиялық факт ретінде қолдануға болмайды."
        ),
        "en": (
            "This is a synthetic GeoKZ demonstration dataset only. "
            "It must not be used as production geological facts."
        ),
    }[language]


def _selection_note(language: SupportedLanguage) -> str:
    return {
        "ru": (
            "Сначала найдите demo-скважины по координате. Затем выберите одну опорную "
            "и минимум одну сравниваемую скважину из returned nearby_demo_wells и повторите "
            "тот же запрос с reference_well_id и well_ids."
        ),
        "kk": (
            "Алдымен координата бойынша demo-ұңғымаларды табыңыз. Содан кейін "
            "nearby_demo_wells ішінен бір тірек және кемінде бір салыстырылатын ұңғыманы "
            "таңдап, сол сұрауды reference_well_id және well_ids мәндерімен қайталаңыз."
        ),
        "en": (
            "First discover demo wells near the coordinate. Then choose one reference well "
            "and at least one compared well from nearby_demo_wells and repeat the same request "
            "with reference_well_id and well_ids."
        ),
    }[language]


def _selection_error(language: SupportedLanguage, code: str) -> str:
    messages = {
        "INCOMPLETE": {
            "ru": "Для построения разреза одновременно укажите reference_well_id и хотя бы один well_id.",
            "kk": "Қиманы құру үшін reference_well_id және кемінде бір well_id бірге көрсетілуі тиіс.",
            "en": "To build a cross-section, provide reference_well_id and at least one well_id together.",
        },
        "DUPLICATE": {
            "ru": "well_ids не должен содержать повторяющиеся скважины.",
            "kk": "well_ids ішінде қайталанатын ұңғымалар болмауы тиіс.",
            "en": "well_ids must not contain duplicate wells.",
        },
        "REFERENCE_IN_COMPARED": {
            "ru": "Опорная скважина не должна одновременно находиться в well_ids.",
            "kk": "Тірек ұңғыма well_ids тізімінде қатар болмауы тиіс.",
            "en": "The reference well must not also appear in well_ids.",
        },
        "OUTSIDE_DISCOVERY": {
            "ru": "Выбирать можно только synthetic/demo скважины, найденные в текущем радиусе поиска.",
            "kk": "Тек ағымдағы іздеу радиусында табылған synthetic/demo ұңғымаларды таңдауға болады.",
            "en": "Only synthetic/demo wells discovered within the current search radius may be selected.",
        },
    }
    return messages[code][language]


@dataclass(slots=True)
class DemoCorrelationWorkflowService:
    session: AsyncSession

    async def run(
        self,
        request: DemoCorrelationWorkflowRequest,
    ) -> DemoCorrelationWorkflowResponse:
        resolved = await CoordinateResolutionService(self.session).resolve(
            request.coordinate
        )
        demo_well_ids = list(
            await self.session.scalars(
                select(Well.id)
                .where(
                    Well.external_id.like(f"{DEMO_CORRELATION_WELL_PREFIX}%"),
                    Well.source_ids.contains([DEMO_CORRELATION_DATASET]),
                )
                .order_by(Well.external_id)
            )
        )

        nearby = await SpatialSearchService(self.session).search_nearby_wells(
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            radius_km=request.radius_km,
            limit=request.limit,
            well_ids=demo_well_ids,
        )
        options = [
            DemoCorrelationWellOption(
                distance_m=item.distance_m,
                well=item.well,
                intervals=item.intervals,
                passport_path=item.passport_path,
            )
            for item in nearby
        ]
        discovered_ids = {item.well.id for item in options}
        suggested_reference_well_id = options[0].well.id if options else None
        can_build_cross_section = len(options) >= 2

        has_reference = request.reference_well_id is not None
        has_compared = bool(request.well_ids)
        if has_reference != has_compared:
            raise DemoCorrelationSelectionError(
                _selection_error(request.language, "INCOMPLETE")
            )

        selection = None
        cross_section = None
        stage = DemoCorrelationWorkflowStage.DISCOVERY
        if has_reference and has_compared:
            assert request.reference_well_id is not None
            if len(set(request.well_ids)) != len(request.well_ids):
                raise DemoCorrelationSelectionError(
                    _selection_error(request.language, "DUPLICATE")
                )
            if request.reference_well_id in request.well_ids:
                raise DemoCorrelationSelectionError(
                    _selection_error(request.language, "REFERENCE_IN_COMPARED")
                )

            selected_ids: set[UUID] = {
                request.reference_well_id,
                *request.well_ids,
            }
            if not selected_ids.issubset(discovered_ids):
                raise DemoCorrelationSelectionError(
                    _selection_error(request.language, "OUTSIDE_DISCOVERY")
                )

            selection = DemoCorrelationSelection(
                reference_well_id=request.reference_well_id,
                compared_well_ids=request.well_ids,
            )
            cross_section = await WellCrossSectionViewService(self.session).build(
                reference_well_id=request.reference_well_id,
                well_ids=request.well_ids,
                language=request.language,
            )
            stage = DemoCorrelationWorkflowStage.CROSS_SECTION_READY

        return DemoCorrelationWorkflowResponse(
            dataset_code=DEMO_CORRELATION_DATASET,
            warning=_synthetic_warning(request.language),
            selection_note=_selection_note(request.language),
            stage=stage,
            resolved_coordinate=resolved,
            nearby_demo_wells=options,
            suggested_reference_well_id=suggested_reference_well_id,
            can_build_cross_section=can_build_cross_section,
            selection_contract=DemoCorrelationSelectionContract(),
            selection=selection,
            cross_section=cross_section,
        )
