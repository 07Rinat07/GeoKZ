import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.core_dataset import CoreDatasetImporter
from app.core.database import AsyncSessionFactory
from app.core.security import hash_password
from app.main import app
from app.models.administrative_region import AdministrativeRegion
from app.models.auth import UserAccount
from app.models.core_dataset import CoreDatasetState
from app.models.enums import UserRole
from app.models.source import Source

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


async def _cleanup_bundled_core_dataset() -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            delete(AdministrativeRegion).where(
                AdministrativeRegion.external_id == "geokz-core:region:kazakhstan"
            )
        )
        await session.execute(
            delete(Source).where(Source.external_id == "geokz-core:source:bootstrap")
        )
        await session.execute(
            delete(CoreDatasetState).where(CoreDatasetState.dataset_code == "geokz-core")
        )
        await session.commit()


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    username = f"core-admin-{uuid4().hex[:10]}"
    password = "GeoKZ-Core-Admin-2026!"
    async with AsyncSessionFactory() as session:
        session.add(
            UserAccount(
                username=username,
                display_name="Core Dataset integration admin",
                role=UserRole.ADMIN,
                password_hash=hash_password(password),
                is_active=True,
            )
        )
        await session.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_bundled_core_dataset_api_installs_idempotently() -> None:
    await _cleanup_bundled_core_dataset()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = await _admin_headers(client)
            initial = await client.get("/api/v1/core-dataset/status")
            assert initial.status_code == 200, initial.text
            initial_payload = initial.json()
            assert initial_payload["bundled_version"] == "2026.09.0-bootstrap"
            assert initial_payload["installed"] is None
            assert initial_payload["update_available"] is True

            dry_run = await client.post(
                "/api/v1/core-dataset/install",
                params={"dry_run": "true", "lang": "en"},
                headers=headers,
            )
            assert dry_run.status_code == 200, dry_run.text
            assert dry_run.json()["dry_run"] is True
            assert dry_run.json()["changed"] is True

            async with AsyncSessionFactory() as session:
                state_after_dry_run = await session.scalar(
                    select(CoreDatasetState).where(CoreDatasetState.dataset_code == "geokz-core")
                )
                assert state_after_dry_run is None

            installed = await client.post(
                "/api/v1/core-dataset/install",
                params={"lang": "kk"},
                headers=headers,
            )
            assert installed.status_code == 200, installed.text
            installed_payload = installed.json()
            assert installed_payload["changed"] is True
            assert installed_payload["dry_run"] is False
            assert installed_payload["item_counts"] == {
                "sources": 1,
                "regions": 1,
                "entities": 0,
                "facts": 0,
            }
            assert "орнатылды" in installed_payload["message"]

            status_response = await client.get("/api/v1/core-dataset/status")
            assert status_response.status_code == 200, status_response.text
            status_payload = status_response.json()
            assert status_payload["installed"]["dataset_version"] == "2026.09.0-bootstrap"
            assert status_payload["update_available"] is False

            repeated = await client.post(
                "/api/v1/core-dataset/install",
                params={"lang": "ru"},
                headers=headers,
            )
            assert repeated.status_code == 200, repeated.text
            assert repeated.json()["changed"] is False

        async with AsyncSessionFactory() as session:
            source_count = await session.scalar(
                select(func.count()).select_from(Source).where(
                    Source.external_id == "geokz-core:source:bootstrap"
                )
            )
            region_count = await session.scalar(
                select(func.count()).select_from(AdministrativeRegion).where(
                    AdministrativeRegion.external_id == "geokz-core:region:kazakhstan"
                )
            )
            state_count = await session.scalar(
                select(func.count()).select_from(CoreDatasetState).where(
                    CoreDatasetState.dataset_code == "geokz-core"
                )
            )
            assert source_count == 1
            assert region_count == 1
            assert state_count == 1
    finally:
        await _cleanup_bundled_core_dataset()


@pytest.mark.asyncio
async def test_core_dataset_import_rolls_back_partial_writes_on_database_error(
    tmp_path: Path,
) -> None:
    suffix = uuid4().hex[:10]
    prefix = f"geokz-core-rollback:{suffix}:"
    dataset_code = f"geokz-core-rollback-{suffix}"
    source_external_id = f"{prefix}source"
    region_external_id = f"{prefix}region"

    source_path = tmp_path / "sources.jsonl"
    source_path.write_text(
        json.dumps(
            {
                "external_id": source_external_id,
                "title": "Rollback integration test source",
                "document_type": "dataset",
                "access_level": "LOCAL",
                "reliability_level": "A",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    region_path = tmp_path / "regions.geojson"
    region_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "external_id": region_external_id,
                            "level": "test",
                            "name_ru": "Rollback region",
                            "parent_external_id": None,
                        },
                        "geometry": {"type": "Point", "coordinates": [71.4, 51.1]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_code": dataset_code,
                "dataset_version": "rollback-test",
                "schema_version": 1,
                "created_at": "2026-09-05T00:00:00Z",
                "external_id_prefix": prefix,
                "dependencies": {},
                "files": [
                    {
                        "path": source_path.name,
                        "kind": "sources",
                        "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    },
                    {
                        "path": region_path.name,
                        "kind": "regions",
                        "sha256": hashlib.sha256(region_path.read_bytes()).hexdigest(),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    async with AsyncSessionFactory() as session:
        with pytest.raises(SQLAlchemyError):
            await CoreDatasetImporter(session).import_bundle(manifest_path)

    async with AsyncSessionFactory() as session:
        assert (
            await session.scalar(select(Source).where(Source.external_id == source_external_id))
            is None
        )
        assert (
            await session.scalar(
                select(AdministrativeRegion).where(
                    AdministrativeRegion.external_id == region_external_id
                )
            )
            is None
        )
        assert (
            await session.scalar(
                select(CoreDatasetState).where(CoreDatasetState.dataset_code == dataset_code)
            )
            is None
        )
