import os
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.domain_vocabulary import DomainVocabularyNormalizer
from app.core.database import AsyncSessionFactory
from app.models.correlation import WellMarker
from app.models.entity import GeologicalEntity
from app.models.enums import (
    DepthReference,
    VerificationStatus,
    VocabularyCode,
    WellType,
)
from app.models.subsurface import CoreRun, CoreSample, WellLogCurve, WellLogRun, WellTest
from app.models.vocabulary import ControlledVocabularyTerm
from app.models.well import Well, WellInterval
from app.schemas.vocabulary import VocabularyResolutionStatus

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_domain_vocabulary_normalizer_preserves_raw_and_assigns_only_safe_codes() -> None:
    suffix = uuid4().hex[:10]

    async with AsyncSessionFactory() as session:
        session.add_all(
            [
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.LITHOLOGY,
                    code=f"sandstone_{suffix}",
                    name_ru=f"Песчаник {suffix}",
                    name_kk=f"Құмтас {suffix}",
                    name_en=f"Sandstone {suffix}",
                    aliases=[f"Sand Stone {suffix}"],
                    source_reference="GeoKZ integration test fixture",
                ),
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.MARKER_TYPE,
                    code=f"stratigraphic_{suffix}",
                    name_ru=f"Стратиграфический репер {suffix}",
                    name_kk=f"Стратиграфиялық репер {suffix}",
                    name_en=f"Stratigraphic marker {suffix}",
                    aliases=[f"Strat Marker {suffix}"],
                    source_reference="GeoKZ integration test fixture",
                ),
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.PROPERTY_KIND,
                    code=f"gamma_ray_{suffix}",
                    name_ru=f"Гамма-каротаж {suffix}",
                    name_kk=f"Гамма-каротаж {suffix}",
                    name_en=f"Gamma ray {suffix}",
                    aliases=[f"GR-{suffix}"],
                    source_reference="GeoKZ integration test fixture",
                ),
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.UNIT,
                    code=f"m3_day_{suffix}",
                    name_ru=f"м3/сут {suffix}",
                    name_kk=f"м3/тәул {suffix}",
                    name_en=f"m3/day {suffix}",
                    aliases=[f"m3/day-{suffix}"],
                    source_reference="GeoKZ integration test fixture",
                    metadata_payload={"symbol": "m3/day", "quantity_kind": "flow"},
                ),
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.UNIT,
                    code=f"bbl_day_{suffix}",
                    name_ru=f"барр/сут {suffix}",
                    name_kk=f"барр/тәул {suffix}",
                    name_en=f"bbl/day {suffix}",
                    aliases=[f"bbl/day-{suffix}"],
                    source_reference="GeoKZ integration test fixture",
                    metadata_payload={"symbol": "bbl/day", "quantity_kind": "flow"},
                ),
            ]
        )

        field = GeologicalEntity(
            external_id=f"it-vocab-field-{suffix}",
            object_type="field",
            name_ru=f"Vocabulary field {suffix}",
            verification_status=VerificationStatus.DRAFT,
        )
        well_entity = GeologicalEntity(
            external_id=f"it-vocab-well-entity-{suffix}",
            object_type="well",
            name_ru=f"Vocabulary well {suffix}",
            verification_status=VerificationStatus.DRAFT,
        )
        session.add_all([field, well_entity])
        await session.flush()

        well = Well(
            external_id=f"it-vocab-well-{suffix}",
            entity_id=well_entity.id,
            object_entity_id=field.id,
            name=f"VOCAB-{suffix}",
            well_type=WellType.EXPLORATION,
            verification_status=VerificationStatus.DRAFT,
        )
        session.add(well)
        await session.flush()

        interval = WellInterval(
            external_id=f"it-vocab-interval-{suffix}",
            well_id=well.id,
            top_depth_m=Decimal("1000"),
            base_depth_m=Decimal("1010"),
            depth_reference=DepthReference.MD,
            lithologies=[f"Sand Stone {suffix}", f"Unknown rock {suffix}"],
            lithology_codes=["reviewed-existing-code"],
            flow_rate=Decimal("10"),
            flow_rate_unit=f"m3/day-{suffix}",
            verification_status=VerificationStatus.DRAFT,
        )
        marker = WellMarker(
            well_id=well.id,
            marker_code=f"M-{suffix}",
            marker_type=f"Strat Marker {suffix}",
            depth_m=Decimal("1005"),
            depth_reference=DepthReference.MD,
            verification_status=VerificationStatus.DRAFT,
        )
        log_run = WellLogRun(
            external_id=f"it-vocab-log-run-{suffix}",
            well_id=well.id,
            name=f"LOG-{suffix}",
            acquisition_type="wireline",
            top_depth_m=Decimal("900"),
            base_depth_m=Decimal("1100"),
            depth_reference=DepthReference.MD,
            verification_status=VerificationStatus.DRAFT,
        )
        core_run = CoreRun(
            external_id=f"it-vocab-core-run-{suffix}",
            well_id=well.id,
            top_depth_m=Decimal("1000"),
            base_depth_m=Decimal("1010"),
            depth_reference=DepthReference.MD,
        )
        well_test = WellTest(
            external_id=f"it-vocab-test-{suffix}",
            well_id=well.id,
            test_type="flow",
            top_depth_m=Decimal("1000"),
            base_depth_m=Decimal("1010"),
            depth_reference=DepthReference.MD,
            oil_rate=Decimal("5"),
            oil_rate_unit=f"bbl/day-{suffix}",
            gas_rate=Decimal("6"),
            gas_rate_unit=f"m3/day-{suffix}",
            water_rate=Decimal("7"),
            water_rate_unit=f"unknown-unit-{suffix}",
            water_rate_unit_code="reviewed-water-unit",
            verification_status=VerificationStatus.DRAFT,
        )
        session.add_all([interval, marker, log_run, core_run, well_test])
        await session.flush()

        curve = WellLogCurve(
            log_run_id=log_run.id,
            mnemonic_original=f"GR-{suffix}",
            property_kind=f"GR-{suffix}",
            unit_original=f"m3/day-{suffix}",
        )
        core_sample = CoreSample(
            core_run_id=core_run.id,
            depth_m=Decimal("1005"),
            lithologies=[f"Sand Stone {suffix}"],
        )
        session.add_all([curve, core_sample])
        await session.flush()

        normalizer = DomainVocabularyNormalizer(session)
        interval_report = await normalizer.normalize_well_interval(interval)
        marker_report = await normalizer.normalize_well_marker(marker)
        curve_report = await normalizer.normalize_well_log_curve(curve)
        sample_report = await normalizer.normalize_core_sample(core_sample)
        test_report = await normalizer.normalize_well_test(well_test)
        await session.commit()

        assert interval.lithologies == [
            f"Sand Stone {suffix}",
            f"Unknown rock {suffix}",
        ]
        assert interval.lithology_codes == ["reviewed-existing-code"]
        assert interval.flow_rate_unit == f"m3/day-{suffix}"
        assert interval.flow_rate_unit_code == f"m3_day_{suffix}"
        assert interval_report.fully_resolved is False
        assert interval_report.issues[0].status == VocabularyResolutionStatus.UNRESOLVED

        assert marker.marker_type == f"Strat Marker {suffix}"
        assert marker.marker_type_code == f"stratigraphic_{suffix}"
        assert marker_report.fully_resolved is True

        assert curve.property_kind == f"GR-{suffix}"
        assert curve.property_kind_code == f"gamma_ray_{suffix}"
        assert curve.unit_original == f"m3/day-{suffix}"
        assert curve.unit_code == f"m3_day_{suffix}"
        assert curve_report.fully_resolved is True

        assert core_sample.lithologies == [f"Sand Stone {suffix}"]
        assert core_sample.lithology_codes == [f"sandstone_{suffix}"]
        assert sample_report.fully_resolved is True

        assert well_test.oil_rate_unit == f"bbl/day-{suffix}"
        assert well_test.oil_rate_unit_code == f"bbl_day_{suffix}"
        assert well_test.gas_rate_unit == f"m3/day-{suffix}"
        assert well_test.gas_rate_unit_code == f"m3_day_{suffix}"
        assert well_test.water_rate_unit == f"unknown-unit-{suffix}"
        assert well_test.water_rate_unit_code == "reviewed-water-unit"
        assert test_report.fully_resolved is False
        assert test_report.issues[0].field_name == "water_rate_unit_code"
