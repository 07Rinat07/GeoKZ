from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.vocabularies import ControlledVocabularyService
from app.models.correlation import WellMarker
from app.models.enums import VocabularyCode
from app.models.subsurface import CoreSample, WellLogCurve, WellTest
from app.models.well import WellInterval
from app.schemas.vocabulary import VocabularyResolutionStatus


@dataclass(frozen=True, slots=True)
class VocabularyNormalizationIssue:
    field_name: str
    raw_value: str
    status: VocabularyResolutionStatus


@dataclass(slots=True)
class DomainVocabularyNormalizationReport:
    updated_fields: list[str] = field(default_factory=list)
    issues: list[VocabularyNormalizationIssue] = field(default_factory=list)

    @property
    def fully_resolved(self) -> bool:
        return not self.issues


@dataclass(slots=True)
class DomainVocabularyNormalizer:
    """Assign canonical vocabulary codes while preserving every raw/source field.

    Only deterministic RESOLVED values are written. UNRESOLVED/AMBIGUOUS values are
    reported and leave an existing canonical assignment untouched. For list fields the
    assignment is atomic: if any raw item is unresolved, the whole canonical list stays
    unchanged so a partial normalization cannot look complete.
    """

    session: AsyncSession

    async def normalize_well_interval(
        self,
        interval: WellInterval,
    ) -> DomainVocabularyNormalizationReport:
        report = DomainVocabularyNormalizationReport()
        await self._assign_list(
            report=report,
            field_name="lithology_codes",
            raw_values=interval.lithologies,
            vocabulary=VocabularyCode.LITHOLOGY,
            assign=lambda codes: setattr(interval, "lithology_codes", codes),
        )
        await self._assign_scalar(
            report=report,
            field_name="flow_rate_unit_code",
            raw_value=interval.flow_rate_unit,
            vocabulary=VocabularyCode.UNIT,
            assign=lambda code: setattr(interval, "flow_rate_unit_code", code),
        )
        return report

    async def normalize_core_sample(
        self,
        sample: CoreSample,
    ) -> DomainVocabularyNormalizationReport:
        report = DomainVocabularyNormalizationReport()
        await self._assign_list(
            report=report,
            field_name="lithology_codes",
            raw_values=sample.lithologies,
            vocabulary=VocabularyCode.LITHOLOGY,
            assign=lambda codes: setattr(sample, "lithology_codes", codes),
        )
        return report

    async def normalize_well_marker(
        self,
        marker: WellMarker,
    ) -> DomainVocabularyNormalizationReport:
        report = DomainVocabularyNormalizationReport()
        await self._assign_scalar(
            report=report,
            field_name="marker_type_code",
            raw_value=marker.marker_type,
            vocabulary=VocabularyCode.MARKER_TYPE,
            assign=lambda code: setattr(marker, "marker_type_code", code),
        )
        return report

    async def normalize_well_log_curve(
        self,
        curve: WellLogCurve,
    ) -> DomainVocabularyNormalizationReport:
        report = DomainVocabularyNormalizationReport()
        await self._assign_scalar(
            report=report,
            field_name="property_kind_code",
            raw_value=curve.property_kind,
            vocabulary=VocabularyCode.PROPERTY_KIND,
            assign=lambda code: setattr(curve, "property_kind_code", code),
        )
        unit_source = curve.canonical_unit or curve.unit_original
        await self._assign_scalar(
            report=report,
            field_name="unit_code",
            raw_value=unit_source,
            vocabulary=VocabularyCode.UNIT,
            assign=lambda code: setattr(curve, "unit_code", code),
        )
        return report

    async def normalize_well_test(
        self,
        well_test: WellTest,
    ) -> DomainVocabularyNormalizationReport:
        report = DomainVocabularyNormalizationReport()
        for field_name, raw_value in (
            ("oil_rate_unit_code", well_test.oil_rate_unit),
            ("gas_rate_unit_code", well_test.gas_rate_unit),
            ("water_rate_unit_code", well_test.water_rate_unit),
        ):
            await self._assign_scalar(
                report=report,
                field_name=field_name,
                raw_value=raw_value,
                vocabulary=VocabularyCode.UNIT,
                assign=lambda code, target=field_name: setattr(well_test, target, code),
            )
        return report

    async def _assign_scalar(
        self,
        *,
        report: DomainVocabularyNormalizationReport,
        field_name: str,
        raw_value: str | None,
        vocabulary: VocabularyCode,
        assign,
    ) -> None:
        if raw_value is None or not raw_value.strip():
            return
        response = await ControlledVocabularyService(self.session).resolve(
            vocabulary=vocabulary,
            values=[raw_value],
            language="en",
        )
        result = response.results[0]
        if result.status == VocabularyResolutionStatus.RESOLVED:
            assert result.term is not None
            assign(result.term.code)
            report.updated_fields.append(field_name)
            return
        report.issues.append(
            VocabularyNormalizationIssue(
                field_name=field_name,
                raw_value=raw_value,
                status=result.status,
            )
        )

    async def _assign_list(
        self,
        *,
        report: DomainVocabularyNormalizationReport,
        field_name: str,
        raw_values: list[str],
        vocabulary: VocabularyCode,
        assign,
    ) -> None:
        if not raw_values:
            assign([])
            report.updated_fields.append(field_name)
            return

        response = await ControlledVocabularyService(self.session).resolve(
            vocabulary=vocabulary,
            values=raw_values,
            language="en",
        )
        codes: list[str] = []
        issues: list[VocabularyNormalizationIssue] = []
        for result in response.results:
            if result.status == VocabularyResolutionStatus.RESOLVED:
                assert result.term is not None
                if result.term.code not in codes:
                    codes.append(result.term.code)
                continue
            issues.append(
                VocabularyNormalizationIssue(
                    field_name=field_name,
                    raw_value=result.input_value,
                    status=result.status,
                )
            )

        if issues:
            report.issues.extend(issues)
            return

        assign(codes)
        report.updated_fields.append(field_name)
