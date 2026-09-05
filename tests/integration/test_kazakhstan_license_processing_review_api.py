import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.integrations.checksum import calculate_payload_checksum
from app.integrations.types import ExternalRecordStatus
from app.main import app
from app.models.integration import ExternalDataSource, ExternalEntityLink, ExternalRecord

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for integration tests",
)


@pytest.mark.asyncio
async def test_license_process_and_record_level_review_api() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    transport = ASGITransport(app=app)
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    external_id = f"it-license-{uuid4()}"

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            register_response = await client.post(
                "/api/v1/integrations/kazakhstan/register?lang=ru"
            )
            assert register_response.status_code == 200, register_response.text

            async with session_factory() as session:
                source = await session.scalar(
                    select(ExternalDataSource).where(
                        ExternalDataSource.code == "kz-egov-geological-study-licenses"
                    )
                )
                assert source is not None
                raw = {
                    "Вид лицензии на недропользование": (
                        "Геологическое изучение недр (углеводородное сырье)"
                    ),
                    "Номер и дата лицензии на недропользование": (
                        "№901-ГИН (УВС) от 05.09.2026 г."
                    ),
                    "Срок лицензии на недропользование": "3 года",
                    "Основание выдачи лицензии на недропользование": (
                        "Заявление ТОО «INTEGRATION LICENSE HOLDER»"
                    ),
                    "Наименование государственного органа, выдавшего лицензию на недропользование": (
                        "Комитет геологии Министерства промышленности и строительства РК"
                    ),
                    "Сведения о лице, которому выдана лицензия на недропользование": (
                        "ТОО «INTEGRATION LICENSE HOLDER»; БИН: 123456789012"
                    ),
                }
                record = ExternalRecord(
                    source_id=source.id,
                    external_id=external_id,
                    record_type="geological_study_license",
                    language="ru",
                    raw_payload=raw,
                    checksum=calculate_payload_checksum(raw),
                    status=ExternalRecordStatus.STAGED,
                )
                session.add(record)
                await session.commit()
                record_id = record.id

            process_response = await client.post(
                "/api/v1/integrations/kazakhstan/"
                "kz-egov-geological-study-licenses/process"
            )
            assert process_response.status_code == 200, process_response.text
            process_payload = process_response.json()
            assert process_payload["normalized"] >= 1
            assert process_payload["review_required"] >= 1
            assert process_payload["exact_matches"] == 0

            queue_response = await client.get(
                "/api/v1/integrations/kazakhstan/"
                "kz-egov-geological-study-licenses/review/records"
            )
            assert queue_response.status_code == 200, queue_response.text
            items = queue_response.json()
            item = next(row for row in items if row["external_id"] == external_id)
            assert item["status"] == "REVIEW_REQUIRED"
            assert item["normalized_payload"]["license_number"] == "№901-ГИН (УВС)"
            assert item["normalized_payload"]["issue_date"] == "2026-09-05"
            assert item["normalized_payload"]["holder_bin"] == "123456789012"
            assert item["normalized_payload"]["review"]["entity_matching"] == (
                "NOT_APPLICABLE"
            )

            accept_response = await client.post(
                "/api/v1/integrations/kazakhstan/"
                "kz-egov-geological-study-licenses/review/records/"
                f"{record_id}/accept",
                json={
                    "reviewer": "Integration Reviewer",
                    "comment": "Administrative record checked against source payload",
                },
            )
            assert accept_response.status_code == 200, accept_response.text
            accepted = accept_response.json()
            assert accepted["record_status"] == "ACCEPTED"
            assert accepted["reviewed_by"] == "Integration Reviewer"

            async with session_factory() as session:
                persisted = await session.get(ExternalRecord, record_id)
                assert persisted is not None
                assert persisted.status == ExternalRecordStatus.ACCEPTED
                assert persisted.reviewed_by == "Integration Reviewer"
                assert persisted.reviewed_at is not None
                links = list(
                    await session.scalars(
                        select(ExternalEntityLink).where(
                            ExternalEntityLink.external_record_id == record_id
                        )
                    )
                )
                assert links == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_changed_license_requires_fresh_review_and_clears_old_decision() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    external_id = f"it-license-changed-{uuid4()}"

    try:
        async with session_factory() as session:
            source = await session.scalar(
                select(ExternalDataSource).where(
                    ExternalDataSource.code == "kz-egov-geological-study-licenses"
                )
            )
            if source is None:
                source = ExternalDataSource(
                    code="kz-egov-geological-study-licenses",
                    name_ru="Лицензии на геологическое изучение недр",
                    name_kk="Жер қойнауын геологиялық зерттеуге берілген лицензиялар",
                    name_en="Licenses for geological exploration of subsoil",
                    base_url="https://data.egov.kz",
                    source_config={},
                )
                session.add(source)
                await session.flush()

            raw = {
                "license_type": "Геологическое изучение недр (подземные воды)",
                "license_number_date": "№902-ГИН(ПВ) от 05.09.2026 г.",
            }
            record = ExternalRecord(
                source_id=source.id,
                external_id=external_id,
                record_type="geological_study_license",
                language="ru",
                raw_payload=raw,
                checksum=calculate_payload_checksum(raw),
                status=ExternalRecordStatus.CHANGED,
                reviewed_by="Old Reviewer",
                review_comment="Old decision",
            )
            session.add(record)
            await session.commit()

            from app.application.kazakhstan_license_processing import (
                KazakhstanGeologicalStudyLicenseProcessingService,
            )

            summary = await KazakhstanGeologicalStudyLicenseProcessingService(
                session
            ).process()
            await session.refresh(record)
            assert summary.normalized >= 1
            assert record.status == ExternalRecordStatus.REVIEW_REQUIRED
            assert record.reviewed_by is None
            assert record.reviewed_at is None
            assert record.review_comment is None
    finally:
        await engine.dispose()
