import httpx
import pytest

from app.desktop.api_client import GeoKZApiClient, GeoKZApiError
from app.desktop.localization import localization_keys


def test_desktop_localizations_have_identical_keys() -> None:
    keys = localization_keys()
    assert keys["ru"] == keys["kk"] == keys["en"]
    assert len(keys["ru"]) >= 35


def test_desktop_client_keeps_token_in_memory_and_uses_backend_action_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/auth/login":
            return httpx.Response(
                200,
                json={
                    "access_token": "test-secret-token",
                    "expires_at": "2026-09-06T00:00:00Z",
                    "user": {
                        "id": "00000000-0000-0000-0000-000000000001",
                        "username": "expert-user",
                        "display_name": "Expert User",
                        "role": "expert",
                        "is_active": True,
                    },
                },
            )
        if request.url.path.endswith("/confirm"):
            assert request.headers["Authorization"] == "Bearer test-secret-token"
            assert request.content == b'{"comment":"checked"}'
            return httpx.Response(
                200,
                json={
                    "record_id": "00000000-0000-0000-0000-000000000010",
                    "record_status": "ACCEPTED",
                    "link_id": "00000000-0000-0000-0000-000000000011",
                    "link_status": "VERIFIED",
                    "entity_id": "00000000-0000-0000-0000-000000000012",
                    "entity_verification_status": "DRAFT",
                },
            )
        if request.url.path == "/api/v1/auth/logout":
            assert request.headers["Authorization"] == "Bearer test-secret-token"
            return httpx.Response(204)
        return httpx.Response(404, json={"detail": "not found"})

    client = GeoKZApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )
    session = client.login("expert-user", "GeoKZ-Password-2026!")
    assert session.access_token == "test-secret-token"
    assert client.is_authenticated is True
    assert client.current_role == "expert"

    action = {
        "code": "CONFIRM_LINK",
        "label": "Confirm link",
        "method": "POST",
        "path": "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/"
        "review/00000000-0000-0000-0000-000000000010/links/"
        "00000000-0000-0000-0000-000000000011/confirm",
        "enabled": True,
        "disabled_reason": None,
        "required_fields": [],
        "optional_fields": ["comment"],
    }
    result = client.execute_field_review_action(action, values={"comment": "checked"})
    assert result["link_status"] == "VERIFIED"
    assert result["entity_verification_status"] == "DRAFT"

    client.logout()
    assert client.is_authenticated is False
    assert client.current_user is None
    assert len(requests) == 3


def test_desktop_client_refuses_disabled_or_incomplete_actions_without_request() -> None:
    request_count = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(500)

    client = GeoKZApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(GeoKZApiError, match="locked"):
        client.execute_field_review_action(
            {
                "method": "POST",
                "path": "/ignored",
                "enabled": False,
                "disabled_reason": "Reviewer decision is locked",
                "required_fields": [],
            }
        )

    with pytest.raises(GeoKZApiError, match="Missing required action fields: entity_id"):
        client.execute_field_review_action(
            {
                "method": "POST",
                "path": "/ignored",
                "enabled": True,
                "required_fields": ["entity_id"],
            }
        )

    assert request_count == 0


def test_desktop_client_surfaces_http_api_detail() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Authentication required"})

    client = GeoKZApiClient(
        "http://testserver",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(GeoKZApiError) as error_info:
        client.login("expert-user", "GeoKZ-Password-2026!")

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Authentication required"
