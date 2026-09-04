import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.kazakhstan_field_review import KazakhstanOilGasFieldReviewService
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


async def _source(session: AsyncSession) -> ExternalDataSource:
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


async def _record(
    session: AsyncSession,
    source: ExternalDataSource,
    *,
    external_id: str,
    name: str,
    matching_status: str,
) -> ExternalRecord:
    raw = {"Наименование месторождения": name}
    record = ExternalRecord(
        source_id=source.id,
        external_id=external_id,
        record_type="oil_gas_field",
        language="ru",
        raw_payload=raw,
        normalized_payload={
            "schema_version": 1,
            "entity_type": "field",
            "name_ru": name,
            "match_key": name.casefold(),
            "source_field": "Наименование месторождения",
            "matching": {
                "status": matching_status,
                "candidate_entity_ids": [],
            },
        },
        checksum=calculate_payload_checksum(raw),
        status=ExternalRecordStatus.REVIEW_REQUIRED,
    )
    session.add(record)
    await session.flush()
    return record


@pytest.mark.asyncio
async def test_reviewer_rejects_one_candidate_and_confirms_another() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = await _source(session)
            entity_a = GeologicalEntity(
                external_id="it-review-candidate-a",
                object_type="field",
                name_ru="TEST REVIEW CANDIDATE A",
                verification_status=VerificationStatus.VERIFIED,
            )
            entity_b = GeologicalEntity(
                external_id="it-review-candidate-b",
                object_type="field",
                name_ru="TEST REVIEW CANDIDATE B",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add_all([entity_a, entity_b])
            await session.flush()
            record = await _record(
                session,
                source,
                external_id="it-review-ambiguous-record",
                name="TEST REVIEW AMBIGUOUS",
                matching_status="AMBIGUOUS",
            )
            link_a = ExternalEntityLink(
                external_record_id=record.id,
                geological_entity_id=entity_a.id,
                match_method=MatchMethod.EXACT_NAME,
                match_confidence=0.95,
                status=EntityLinkStatus.REVIEW_REQUIRED,
            )
            link_b = ExternalEntityLink(
                external_record_id=record.id,
                geological_entity_id=entity_b.id,
                match_method=MatchMethod.ALIAS,
                match_confidence=0.90,
                status=EntityLinkStatus.REVIEW_REQUIRED,
            )
            session.add_all([link_a, link_b])
            await session.commit()

            service = KazakhstanOilGasFieldReviewService(session)
            rejected = await service.reject_link(
                record_id=record.id,
                link_id=link_a.id,
                reviewer="Integration Reviewer",
                comment="Не тот объект",
            )
            assert rejected.link_status == EntityLinkStatus.REJECTED
            assert rejected.record_status == ExternalRecordStatus.REVIEW_REQUIRED

            confirmed = await service.confirm_link(
                record_id=record.id,
                link_id=link_b.id,
                reviewer="Integration Reviewer",
                comment="Подтверждено по реестру",
            )
            assert confirmed.link_status == EntityLinkStatus.VERIFIED
            assert confirmed.record_status == ExternalRecordStatus.ACCEPTED
            await session.refresh(link_a)
            await session.refresh(link_b)
            assert link_a.status == EntityLinkStatus.REJECTED
            assert link_b.status == EntityLinkStatus.VERIFIED
            assert link_b.verified_by == "Integration Reviewer"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_reviewer_can_manually_link_unmatched_record_to_existing_field() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = await _source(session)
            entity = GeologicalEntity(
                external_id="it-review-manual-field",
                object_type="field",
                name_ru="TEST MANUAL FIELD",
                verification_status=VerificationStatus.REVIEWED,
            )
            session.add(entity)
            await session.flush()
            record = await _record(
                session,
                source,
                external_id="it-review-manual-record",
                name="TEST MANUAL UPSTREAM NAME",
                matching_status="UNMATCHED",
            )
            await session.commit()

            result = await KazakhstanOilGasFieldReviewService(session).manual_link(
                record_id=record.id,
                entity_id=entity.id,
                reviewer="Integration Reviewer",
                comment="Ручное сопоставление",
            )

            link = await session.get(ExternalEntityLink, result.link_id)
            assert result.record_status == ExternalRecordStatus.ACCEPTED
            assert result.entity_id == entity.id
            assert link is not None
            assert link.match_method == MatchMethod.MANUAL
            assert link.status == EntityLinkStatus.VERIFIED
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_reviewer_can_create_only_draft_field_from_unmatched_record() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = await _source(session)
            record = await _record(
                session,
                source,
                external_id="it-review-create-draft-record",
                name="TEST NEW DRAFT FIELD",
                matching_status="UNMATCHED",
            )
            await session.commit()

            result = await KazakhstanOilGasFieldReviewService(session).create_draft_field(
                record_id=record.id,
                reviewer="Integration Reviewer",
                comment="Создать для дальнейшей проверки",
                name_kk="TEST ЖАҢА DRAFT КЕН ОРНЫ",
                name_en="TEST NEW DRAFT FIELD",
            )

            entity = await session.get(GeologicalEntity, result.entity_id)
            link = await session.get(ExternalEntityLink, result.link_id)
            assert result.record_status == ExternalRecordStatus.ACCEPTED
            assert result.entity_verification_status == VerificationStatus.DRAFT
            assert entity is not None
            assert entity.object_type == "field"
            assert entity.name_ru == "TEST NEW DRAFT FIELD"
            assert entity.verification_status == VerificationStatus.DRAFT
            assert entity.geological_context["origin"] == "external_review_draft"
            assert link is not None
            assert link.match_method == MatchMethod.MANUAL
            assert link.status == EntityLinkStatus.VERIFIED
    finally:
        await engine.dispose()
