import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionFactory
from app.core.security import hash_password
from app.main import app
from app.models.auth import UserAccount
from app.models.enums import UserRole

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


async def _headers_for_role(client: AsyncClient, role: UserRole) -> dict[str, str]:
    username = f"core-update-{role.value}-{uuid4().hex[:10]}"
    password = "GeoKZ-Core-Update-2026!"
    async with AsyncSessionFactory() as session:
        session.add(
            UserAccount(
                username=username,
                display_name=f"Core update {role.value}",
                role=role,
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
async def test_core_dataset_update_status_is_admin_only_and_disabled_by_default() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauthenticated = await client.get("/api/v1/core-dataset/update/status")
        assert unauthenticated.status_code == 401

        editor_headers = await _headers_for_role(client, UserRole.EDITOR)
        forbidden = await client.get(
            "/api/v1/core-dataset/update/status",
            headers=editor_headers,
        )
        assert forbidden.status_code == 403

        admin_headers = await _headers_for_role(client, UserRole.ADMIN)
        response = await client.get(
            "/api/v1/core-dataset/update/status",
            headers=admin_headers,
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["configured"] is False
    assert payload["state"] == "DISABLED"
    assert payload["signature_verified"] is False
    assert payload["compatible"] is False
    assert "rollback_available" in payload
