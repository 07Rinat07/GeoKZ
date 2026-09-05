import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionFactory
from app.main import app
from app.models.enums import VocabularyCode
from app.models.vocabulary import ControlledVocabularyTerm

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_vocabulary_api_lists_and_resolves_only_active_terms() -> None:
    suffix = uuid4().hex[:10]
    active_code = f"it_sandstone_{suffix}"
    inactive_code = f"it_inactive_{suffix}"
    alias = f"IT Sandstone Alias {suffix}"

    async with AsyncSessionFactory() as session:
        session.add_all(
            [
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.LITHOLOGY,
                    code=active_code,
                    name_ru=f"Интеграционный песчаник {suffix}",
                    name_kk=f"Интеграциялық құмтас {suffix}",
                    name_en=f"Integration sandstone {suffix}",
                    aliases=[alias],
                    source_reference="GeoKZ integration test fixture",
                    metadata_payload={"fixture": True},
                    is_active=True,
                ),
                ControlledVocabularyTerm(
                    vocabulary=VocabularyCode.LITHOLOGY,
                    code=inactive_code,
                    name_ru=f"Неактивная порода {suffix}",
                    name_kk=f"Белсенді емес жыныс {suffix}",
                    name_en=f"Inactive rock {suffix}",
                    aliases=[],
                    source_reference="GeoKZ integration test fixture",
                    metadata_payload={"fixture": True},
                    is_active=False,
                ),
            ]
        )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get(
            "/api/v1/vocabularies/lithology/terms",
            params={"lang": "kk"},
        )
        assert list_response.status_code == 200, list_response.text
        terms = list_response.json()
        active = next(item for item in terms if item["code"] == active_code)
        assert active["display_name"] == f"Интеграциялық құмтас {suffix}"
        assert all(item["code"] != inactive_code for item in terms)

        include_inactive_response = await client.get(
            "/api/v1/vocabularies/lithology/terms",
            params={"lang": "en", "include_inactive": "true"},
        )
        assert include_inactive_response.status_code == 200
        assert any(
            item["code"] == inactive_code
            for item in include_inactive_response.json()
        )

        resolve_response = await client.post(
            "/api/v1/vocabularies/lithology/resolve",
            params={"lang": "ru"},
            json={"values": [alias.swapcase(), active_code.upper(), inactive_code, "not known"]},
        )
        assert resolve_response.status_code == 200, resolve_response.text
        results = resolve_response.json()["results"]
        assert results[0]["status"] == "RESOLVED"
        assert results[0]["term"]["code"] == active_code
        assert results[1]["status"] == "RESOLVED"
        assert results[1]["term"]["code"] == active_code
        assert results[2]["status"] == "UNRESOLVED"
        assert results[3]["status"] == "UNRESOLVED"

        catalog_response = await client.get(
            "/api/v1/vocabularies",
            params={"lang": "ru"},
        )
        assert catalog_response.status_code == 200
        catalog = catalog_response.json()
        assert {item["vocabulary"] for item in catalog} == {
            item.value for item in VocabularyCode
        }
