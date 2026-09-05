import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.integrations.checksum import calculate_payload_checksum
from app.integrations.types import EntityLinkStatus, ExternalRecordStatus, MatchMethod
from app.main import app
from app.models.auth import UserAccount
from app.models.entity import GeologicalEntity
from app.models.enums import UserRole, VerificationStatus
from app.models.integration import ExternalDataSource, ExternalEntityLink, ExternalRecord

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for integration tests",
)


@pytest.mark.asyncio
async def test_review_view_endpoint_returns_localized_actionable_contract() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    suffix = uuid4().hex[:10]
    username = f"review-view-{suffix}"
    password = "GeoKZ-Review-View-2026!"

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

            session.add(
                UserAccount(
                    username=username,
                    display_name="Field review view integration user",
                    role=UserRole.EDITOR,
                    password_hash=hash_password(password),
                    is_active=True,
                )
            )

            entity = GeologicalEntity(
                external_id=f"it-review-view-field-{suffix}",
                object_type="field",
                name_ru="TEST REVIEW VIEW RU",
                name_kk="TEST REVIEW VIEW KK",
                name_en="TEST REVIEW VIEW EN",
                verification_status=VerificationStatus.VERIFIED,
            )
            session.add(entity)
            await session.flush()

            payload = {"name": "TEST REVIEW VIEW UPSTREAM"}
            record = ExternalRecord(
                source_id=source.id,
                external_id=f"it-review-view-record-{suffix}",
                record_type="oil_gas_field",
                language="ru",
                raw_payload=payload,
                normalized_payload={
                    "schema_version": 1,
                    "entity_type": "field",
                    "name_ru": "TEST REVIEW VIEW UPSTREAM",
                    "matching": {
                        "status": "CANDIDATE",
                        "candidate_entity_ids": [str(entity.id)],
                    },
                },
                checksum=calculate_payload_checksum(payload),
                status=ExternalRecordStatus.REVIEW_REQUIRED,
            )
            session.add(record)
            await session.flush()

            link = ExternalEntityLink(
                external_record_id=record.id,
                geological_entity_id=entity.id,
                match_method=MatchMethod.EXACT_NAME,
                match_confidence=1.0,
                status=EntityLinkStatus.REVIEW_REQUIRED,
            )
            session.add(link)
            await session.commit()
            external_id = record.external_id

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            assert login.status_code == 200, login.text
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
            response = await client.get(
                "/api/v1/integrations/kazakhstan/"
                "kz-egov-oil-gas-fields/review/view?lang=kk&limit=200",
                headers=headers,
            )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["source_code"] == "kz-egov-oil-gas-fields"
        assert body["language"] == "kk"
        assert body["total_pending"] >= 1

        item = next(
            record_item
            for record_item in body["records"]
            if record_item["external_id"] == external_id
        )
        assert item["matching_status"] == "CANDIDATE"
        assert item["display_name"] == "TEST REVIEW VIEW UPSTREAM"
        assert item["candidates"][0]["entity_display_name"] == "TEST REVIEW VIEW KK"
        assert item["candidates"][0]["entity_verification_status"] == "VERIFIED"

        candidate_actions = {
            action["code"]: action for action in item["candidates"][0]["actions"]
        }
        assert candidate_actions["CONFIRM_LINK"]["enabled"] is True
        assert candidate_actions["CONFIRM_LINK"]["required_fields"] == []
        assert candidate_actions["REJECT_LINK"]["enabled"] is True
        assert candidate_actions["REJECT_LINK"]["required_fields"] == ["comment"]

        record_actions = {action["code"]: action for action in item["actions"]}
        assert record_actions["MANUAL_LINK"]["enabled"] is True
        assert record_actions["MANUAL_LINK"]["required_fields"] == ["entity_id"]
        assert record_actions["CREATE_DRAFT_FIELD"]["enabled"] is False
    finally:
        await engine.dispose()
