import os
import warnings
from decimal import Decimal

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import SAWarning
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.correlation import WellCorrelationService
from app.models.entity import GeologicalEntity
from app.models.enums import VerificationStatus, WellType
from app.models.well import Well

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_distance_query_has_no_cartesian_warning_and_preserves_postgis_distance() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            field = GeologicalEntity(
                external_id="it-distance-warning-field",
                object_type="field",
                name_ru="Distance warning field",
                verification_status=VerificationStatus.VERIFIED,
            )
            reference_entity = GeologicalEntity(
                external_id="it-distance-warning-reference-entity",
                object_type="well",
                name_ru="Reference well",
                verification_status=VerificationStatus.VERIFIED,
            )
            candidate_entity = GeologicalEntity(
                external_id="it-distance-warning-candidate-entity",
                object_type="well",
                name_ru="Candidate well",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([field, reference_entity, candidate_entity])
            await session.flush()

            reference_well = Well(
                external_id="it-distance-warning-reference",
                entity_id=reference_entity.id,
                object_entity_id=field.id,
                name="REF-DIST",
                well_type=WellType.EXPLORATION,
                total_depth_m=Decimal("3000"),
                location=WKTElement("POINT(51.168420 43.652341)", srid=4326),
                verification_status=VerificationStatus.VERIFIED,
            )
            candidate_well = Well(
                external_id="it-distance-warning-candidate",
                entity_id=candidate_entity.id,
                object_entity_id=field.id,
                name="CAND-DIST",
                well_type=WellType.EXPLORATION,
                total_depth_m=Decimal("3050"),
                location=WKTElement("POINT(51.180000 43.652341)", srid=4326),
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([reference_well, candidate_well])
            await session.commit()

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", SAWarning)
                distances = await WellCorrelationService(session)._distances(
                    reference_well.id,
                    [reference_well.id, candidate_well.id],
                )

            cartesian_warnings = [
                warning
                for warning in caught
                if issubclass(warning.category, SAWarning)
                and "cartesian product" in str(warning.message).casefold()
            ]
            assert cartesian_warnings == []
            assert distances[reference_well.id] == 0.0
            candidate_distance = distances[candidate_well.id]
            assert candidate_distance is not None
            assert 800 < candidate_distance < 1100
    finally:
        await engine.dispose()
