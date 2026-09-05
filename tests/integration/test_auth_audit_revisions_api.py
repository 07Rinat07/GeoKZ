import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.database import AsyncSessionFactory
from app.core.security import hash_password
from app.main import app
from app.models.audit import AuditLog
from app.models.auth import UserAccount
from app.models.enums import UserRole

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


async def _seed_admin() -> tuple[str, str]:
    suffix = uuid4().hex[:10]
    username = f"auth-admin-{suffix}"
    password = "GeoKZ-Auth-Admin-2026!"
    async with AsyncSessionFactory() as session:
        session.add(
            UserAccount(
                username=username,
                display_name="Authentication integration admin",
                role=UserRole.ADMIN,
                password_hash=hash_password(password),
                is_active=True,
            )
        )
        await session.commit()
    return username, password


async def _login(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_auth_rbac_audit_and_revision_history() -> None:
    admin_username, admin_password = await _seed_admin()
    suffix = uuid4().hex[:10]
    editor_username = f"editor-{suffix}"
    expert_username = f"expert-{suffix}"
    editor_password = "GeoKZ-Editor-Password-2026!"
    expert_password = "GeoKZ-Expert-Password-2026!"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauthenticated = await client.get("/api/v1/auth/me")
        assert unauthenticated.status_code == 401

        admin_headers = await _login(client, admin_username, admin_password)
        me = await client.get("/api/v1/auth/me", headers=admin_headers)
        assert me.status_code == 200
        assert me.json()["role"] == "admin"

        for username, password, role in (
            (editor_username, editor_password, "editor"),
            (expert_username, expert_password, "expert"),
        ):
            created = await client.post(
                "/api/v1/auth/users",
                headers=admin_headers,
                json={
                    "username": username,
                    "display_name": f"{role.title()} integration user",
                    "role": role,
                    "password": password,
                },
            )
            assert created.status_code == 201, created.text
            assert created.json()["role"] == role

        editor_headers = await _login(client, editor_username, editor_password)
        expert_headers = await _login(client, expert_username, expert_password)

        source_response = await client.post(
            "/api/v1/sources",
            headers=editor_headers,
            json={
                "external_id": f"auth-test-source:{suffix}",
                "title": "Authentication audit integration source",
                "document_type": "dataset",
                "access_level": "LOCAL",
                "reliability_level": "A",
            },
        )
        assert source_response.status_code == 201, source_response.text
        source_id = source_response.json()["id"]

        entity_response = await client.post(
            "/api/v1/entities",
            headers=editor_headers,
            json={
                "external_id": f"auth-test-entity:{suffix}",
                "object_type": "field",
                "name_ru": f"Тестовое месторождение {suffix}",
                "geometry_status": "UNKNOWN",
                "verification_status": "DRAFT",
            },
        )
        assert entity_response.status_code == 201, entity_response.text
        entity_id = entity_response.json()["id"]

        editor_verify = await client.patch(
            f"/api/v1/entities/{entity_id}",
            headers=editor_headers,
            json={
                "verification_status": "VERIFIED",
                "change_reason": "editor must not verify scientific master data",
            },
        )
        assert editor_verify.status_code == 403

        expert_review = await client.patch(
            f"/api/v1/entities/{entity_id}",
            headers=expert_headers,
            json={
                "verification_status": "REVIEWED",
                "description": "Reviewed by authenticated expert",
                "change_reason": "evidence checked in integration test",
            },
        )
        assert expert_review.status_code == 200, expert_review.text
        assert expert_review.json()["verification_status"] == "REVIEWED"

        revisions = await client.get(
            f"/api/v1/audit/revisions/geological_entity/{entity_id}",
            headers=expert_headers,
        )
        assert revisions.status_code == 200, revisions.text
        revision_rows = revisions.json()
        assert [item["revision_number"] for item in revision_rows] == [1, 2]
        assert revision_rows[0]["action"] == "CREATE"
        assert revision_rows[1]["action"] == "UPDATE"
        assert revision_rows[1]["actor_username"] == expert_username
        assert revision_rows[1]["snapshot"]["verification_status"] == "REVIEWED"

        source_revisions = await client.get(
            f"/api/v1/audit/revisions/source/{source_id}",
            headers=editor_headers,
        )
        assert source_revisions.status_code == 200
        assert len(source_revisions.json()) == 1

        editor_audit_denied = await client.get(
            "/api/v1/audit/logs",
            headers=editor_headers,
        )
        assert editor_audit_denied.status_code == 403

        audit_response = await client.get(
            "/api/v1/audit/logs",
            headers=admin_headers,
            params={"resource_type": "geological_entity", "resource_id": entity_id},
        )
        assert audit_response.status_code == 200, audit_response.text
        actions = {item["action"] for item in audit_response.json()}
        assert {"CREATE", "UPDATE"} <= actions

        logout = await client.post("/api/v1/auth/logout", headers=expert_headers)
        assert logout.status_code == 204
        after_logout = await client.get("/api/v1/auth/me", headers=expert_headers)
        assert after_logout.status_code == 401

    async with AsyncSessionFactory() as session:
        audit_row = await session.scalar(
            select(AuditLog).where(
                AuditLog.resource_type == "geological_entity",
                AuditLog.resource_id == entity_id,
            )
        )
        assert audit_row is not None
        with pytest.raises(DBAPIError):
            await session.execute(
                text("UPDATE audit_logs SET reason = 'tampered' WHERE id = :id"),
                {"id": audit_row.id},
            )
            await session.commit()
        await session.rollback()
