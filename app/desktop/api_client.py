from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    access_token: str
    expires_at: str
    user: JsonObject


class GeoKZApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class GeoKZApiClient:
    """Synchronous HTTP client used by the PySide6 desktop shell.

    Authentication tokens are kept in memory only. The client never talks to the database
    directly and consumes backend-owned review/action contracts as returned by the API.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            raise ValueError("base_url must not be empty")
        self._client = httpx.Client(
            base_url=normalized,
            timeout=timeout_seconds,
            transport=transport,
        )
        self._access_token: str | None = None
        self._current_user: JsonObject | None = None

    @property
    def base_url(self) -> str:
        return str(self._client.base_url).rstrip("/")

    @property
    def is_authenticated(self) -> bool:
        return bool(self._access_token)

    @property
    def current_user(self) -> JsonObject | None:
        return dict(self._current_user) if self._current_user is not None else None

    @property
    def current_role(self) -> str | None:
        if self._current_user is None:
            return None
        role = self._current_user.get("role")
        return role if isinstance(role, str) else None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GeoKZApiClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def login(self, username: str, password: str) -> AuthenticatedSession:
        payload = self._request_json(
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": password},
            authenticated=False,
        )
        token = self._require_string(payload, "access_token")
        expires_at = self._require_string(payload, "expires_at")
        user = payload.get("user")
        if not isinstance(user, dict):
            raise GeoKZApiError("API returned invalid authenticated user payload")
        self._access_token = token
        self._current_user = dict(user)
        return AuthenticatedSession(
            access_token=token,
            expires_at=expires_at,
            user=dict(user),
        )

    def logout(self) -> None:
        try:
            if self._access_token:
                self._request(
                    "POST",
                    "/api/v1/auth/logout",
                    authenticated=True,
                )
        finally:
            self._access_token = None
            self._current_user = None

    def refresh_current_user(self) -> JsonObject:
        payload = self._request_json("GET", "/api/v1/auth/me")
        self._current_user = dict(payload)
        return dict(payload)

    def about(self, language: str) -> JsonObject:
        return self._request_json(
            "GET",
            "/api/v1/about",
            params={"lang": language},
            authenticated=False,
        )

    def core_dataset_status(self) -> JsonObject:
        return self._request_json(
            "GET",
            "/api/v1/core-dataset/status",
            authenticated=False,
        )

    def list_external_sources(self, language: str) -> list[JsonObject]:
        payload = self._request_json_value(
            "GET",
            "/api/v1/integrations/sources",
            params={"lang": language},
            authenticated=False,
        )
        return self._require_object_list(payload, "external sources")

    def scheduler_status(self) -> JsonObject:
        return self._request_json(
            "GET",
            "/api/v1/integrations/scheduler/status",
            authenticated=False,
        )

    def sync_all(self) -> JsonObject:
        return self._request_json("POST", "/api/v1/integrations/sync-all")

    def field_review_queue(
        self,
        language: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> JsonObject:
        return self._request_json(
            "GET",
            "/api/v1/integrations/kazakhstan/"
            "kz-egov-oil-gas-fields/review/view",
            params={"lang": language, "limit": limit, "offset": offset},
        )

    def execute_field_review_action(
        self,
        action: JsonObject,
        *,
        values: JsonObject | None = None,
    ) -> JsonObject:
        enabled = action.get("enabled")
        if enabled is not True:
            reason = action.get("disabled_reason")
            detail = reason if isinstance(reason, str) and reason else "Action is disabled"
            raise GeoKZApiError(detail)
        method = self._require_string(action, "method").upper()
        path = self._require_string(action, "path")
        required_fields = action.get("required_fields", [])
        if not isinstance(required_fields, list) or not all(
            isinstance(item, str) for item in required_fields
        ):
            raise GeoKZApiError("API returned invalid action required_fields")
        payload = dict(values or {})
        missing = [field for field in required_fields if not self._has_value(payload.get(field))]
        if missing:
            raise GeoKZApiError(f"Missing required action fields: {', '.join(missing)}")
        return self._request_json(method, path, json=payload)

    def license_review_queue(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JsonObject]:
        payload = self._request_json_value(
            "GET",
            "/api/v1/integrations/kazakhstan/"
            "kz-egov-geological-study-licenses/review/records",
            params={"limit": limit, "offset": offset},
        )
        return self._require_object_list(payload, "license review records")

    def accept_license_record(self, record_id: str, comment: str | None = None) -> JsonObject:
        return self._request_json(
            "POST",
            "/api/v1/integrations/kazakhstan/"
            f"kz-egov-geological-study-licenses/review/records/{record_id}/accept",
            json={"comment": comment},
        )

    def reject_license_record(self, record_id: str, comment: str) -> JsonObject:
        if not comment.strip():
            raise GeoKZApiError("Reject comment must not be empty")
        return self._request_json(
            "POST",
            "/api/v1/integrations/kazakhstan/"
            f"kz-egov-geological-study-licenses/review/records/{record_id}/reject",
            json={"comment": comment},
        )

    def audit_logs(self, *, limit: int = 100, offset: int = 0) -> list[JsonObject]:
        payload = self._request_json_value(
            "GET",
            "/api/v1/audit/logs",
            params={"limit": limit, "offset": offset},
        )
        return self._require_object_list(payload, "audit logs")

    def revisions(self, resource_type: str, resource_id: str) -> list[JsonObject]:
        payload = self._request_json_value(
            "GET",
            f"/api/v1/audit/revisions/{resource_type}/{resource_id}",
        )
        return self._require_object_list(payload, "revisions")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json: JsonObject | None = None,
        authenticated: bool = True,
    ) -> JsonObject:
        payload = self._request_json_value(
            method,
            path,
            params=params,
            json=json,
            authenticated=authenticated,
        )
        if not isinstance(payload, dict):
            raise GeoKZApiError("API returned JSON with an unexpected type")
        return dict(payload)

    def _request_json_value(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json: JsonObject | None = None,
        authenticated: bool = True,
    ) -> object:
        response = self._request(
            method,
            path,
            params=params,
            json=json,
            authenticated=authenticated,
        )
        try:
            return response.json()
        except ValueError as error:
            raise GeoKZApiError(
                "API returned an invalid JSON response",
                status_code=response.status_code,
            ) from error

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json: JsonObject | None = None,
        authenticated: bool = True,
    ) -> httpx.Response:
        headers: dict[str, str] = {}
        if authenticated:
            if not self._access_token:
                raise GeoKZApiError("Authentication required")
            headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            response = self._client.request(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.HTTPError as error:
            raise GeoKZApiError(f"Cannot reach GeoKZ API: {error}") from error
        if response.is_error:
            detail = self._extract_error_detail(response)
            raise GeoKZApiError(
                detail or f"GeoKZ API returned HTTP {response.status_code}",
                status_code=response.status_code,
                detail=detail,
            )
        return response

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str | None:
        try:
            payload = response.json()
        except ValueError:
            text = response.text.strip()
            return text or None
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str):
                return detail
            if detail is not None:
                return str(detail)
        return None

    @staticmethod
    def _require_string(payload: JsonObject, key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise GeoKZApiError(f"API payload is missing string field: {key}")
        return value

    @staticmethod
    def _require_object_list(payload: object, label: str) -> list[JsonObject]:
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise GeoKZApiError(f"API returned invalid {label} payload")
        return [dict(item) for item in payload]

    @staticmethod
    def _has_value(value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True
