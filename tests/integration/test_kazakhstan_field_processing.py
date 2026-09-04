import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


async def _get_or_create_source(session: AsyncSession) -> ExternalDataSource:
    source = await session.scalar(
        select(ExternalDataSource).where(
            ExternalDataSource.code == "kz-egov-oil-gas-fields"
        )
    )
    if source is not None:
        return source

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
    return source


@pytest.mark.asyncio
async def test_oil_gas_field_processing_creates_review_candidate() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = await _get_or_create_source(session)
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

            service = KazakhstanOilGasFieldProcessingService(session)
            summary = await service.process()

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

            second_summary = await service.process()
            links = list(
                await session.scalars(
                    select(ExternalEntityLink).where(
                        ExternalEntityLink.external_record_id == record.id,
                        ExternalEntityLink.geological_entity_id == entity.id,
                    )
                )
            )
            assert second_summary.normalized >= 1
            assert len(links) == 1
            assert links[0].status == EntityLinkStatus.REVIEW_REQUIRED
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_reprocessing_does_not_overwrite_verified_reviewer_link() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = await _get_or_create_source(session)
            original_entity = GeologicalEntity(
                external_id="it-kz-egov-review-lock-original",
                object_type="field",
                name_ru="TEST REVIEW LOCK A",
                verification_status=VerificationStatus.VERIFIED,
            )
            changed_name_entity = GeologicalEntity(
                external_id="it-kz-egov-review-lock-changed",
                object_type="field",
                name_ru="TEST REVIEW LOCK B",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([original_entity, changed_name_entity])
            await session.flush()

            payload = {"name": "TEST REVIEW LOCK A"}
            record = ExternalRecord(
                source_id=source.id,
                external_id="it-review-lock-record",
                record_type="oil_gas_field",
                language="ru",
                raw_payload=payload,
                checksum=calculate_payload_checksum(payload),
                status=ExternalRecordStatus.STAGED,
            )
            session.add(record)
            await session.commit()

            await KazakhstanOilGasFieldProcessingService(session).process()
            link = await session.scalar(
                select(ExternalEntityLink).where(
                    ExternalEntityLink.external_record_id == record.id,
                    ExternalEntityLink.geological_entity_id == original_entity.id,
                )
            )
            assert link is not None
            link.status = EntityLinkStatus.VERIFIED
            link.verified_by = "integration-test-reviewer"
            await session.commit()

            changed_payload = {"name": "TEST REVIEW LOCK B"}
            record.raw_payload = changed_payload
            record.checksum = calculate_payload_checksum(changed_payload)
            record.status = ExternalRecordStatus.CHANGED
            await session.commit()

            summary = await KazakhstanOilGasFieldProcessingService(session).process()
            await session.refresh(record)

            links = list(
                await session.scalars(
                    select(ExternalEntityLink).where(
                        ExternalEntityLink.external_record_id == record.id
                    )
                )
            )
            assert summary.reviewer_locked >= 1
            assert record.status == ExternalRecordStatus.ACCEPTED
            assert record.normalized_payload is not None
            assert record.normalized_payload["matching"]["status"] == "REVIEWER_LOCKED"
            assert len(links) == 1
            assert links[0].geological_entity_id == original_entity.id
            assert links[0].status == EntityLinkStatus.VERIFIED
    finally:
        await engine.dispose()
