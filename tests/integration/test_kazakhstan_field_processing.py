import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.kazakhstan_field_processing import (
    KazakhstanOilGasFieldProcessingService,
)
from app.integrations.checksum import calculate_payload_checksum
from app.integrations.types import EntityLinkStatus, ExternalRecordStatus, MatchMethod
from app.models.entity import GeologicalEntity
from app.models.enums import VerificationStatus
from app.models.integration import ExternalDataSource, ExternalEntityLink, ExternalRecord

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for integration tests",
)


@pytest.mark.asyncio
async def test_oil_gas_field_processing_creates_review_candidate() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = await session.scalar(
                select(ExternalDataSource).where(
                    ExternalDataSource.code == "kz-egov-oil-gas-fields"
                )
            )
            if source is None:
                source = ExternalDataSource(
                    code="kz-egov-oil-gas-fields",
                    name_ru="Нефтегазовые месторождения Республики Казахстан",
                    name_kk="Қазақстан Республикасының мұнай-газ кен орындары",
                    name_en="Oil and gas fields of the Republic of Kazakhstan",
                    base_url="https://data.egov.kz",
                    source_config={},
                )
                session.add(source)
                await session.flush()

            entity = GeologicalEntity(
                external_id="it-kz-egov-field-test-zhetybai",
                object_type="field",
                name_ru="TEST ЖЕТЫБАЙ",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add(entity)
            await session.flush()

            payload = {"Наименование месторождения": "TEST-ЖЕТЫБАЙ"}
            record = ExternalRecord(
                source_id=source.id,
                external_id="it-test-zhetybai",
                record_type="oil_gas_field",
                language="ru",
                raw_payload=payload,
                checksum=calculate_payload_checksum(payload),
                status=ExternalRecordStatus.STAGED,
            )
            session.add(record)
            await session.commit()

            summary = await KazakhstanOilGasFieldProcessingService(session).process()

            await session.refresh(record)
            link = await session.scalar(
                select(ExternalEntityLink).where(
                    ExternalEntityLink.external_record_id == record.id,
                    ExternalEntityLink.geological_entity_id == entity.id,
                )
            )

            assert summary.normalized >= 1
            assert summary.exact_matches >= 1
            assert record.status == ExternalRecordStatus.REVIEW_REQUIRED
            assert record.normalized_payload is not None
            assert record.normalized_payload["name_ru"] == "TEST-ЖЕТЫБАЙ"
            assert record.normalized_payload["matching"]["status"] == "CANDIDATE"
            assert link is not None
            assert link.match_method == MatchMethod.EXACT_NAME
            assert link.match_confidence == 1.0
            assert link.status == EntityLinkStatus.REVIEW_REQUIRED
    finally:
        await engine.dispose()
