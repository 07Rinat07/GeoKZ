# GeoKZ Desktop — PySide6 client

GeoKZ Desktop is the Windows/desktop client that sits on top of the central GeoKZ HTTP API. The client **does not connect to PostgreSQL directly**, does not import SQLAlchemy models, and does not duplicate scientific verification rules. Review, provenance, authorization and business rules remain owned by the backend.

## Installation

Install the optional desktop dependency for development:

```powershell
python -m pip install -e ".[desktop]"
```

Run the backend separately, for example on `http://127.0.0.1:8000`.

Start the client with:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang en
```

or:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang en
```

Supported interface languages are `ru`, `kk`, and `en`.

## Sign-in and session handling

The desktop client uses:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

The opaque bearer token is stored in process memory only. The client does not persist the password or access token to settings, logs, or files. When the main window closes, the client performs logout and clears its in-memory token state.

Backend roles are `editor`, `expert`, and `admin`. The current user and role are displayed in the UI, but a UI role check is never treated as the security boundary. The backend always re-validates authorization.

## Data Sources screen

The screen aggregates these backend contracts:

```text
GET /api/v1/system/versions
GET /api/v1/about
GET /api/v1/core-dataset/status
GET /api/v1/integrations/sources
GET /api/v1/integrations/scheduler/status
```

It displays:

- application version;
- Alembic/database schema revision;
- bundled Core Dataset version;
- installed Core Dataset version;
- provider/dataset version;
- due/running/error status;
- last successful synchronization time;
- last provider error.

The “Update all” action invokes `POST /api/v1/integrations/sync-all`. External synchronization updates RAW/staging data and synchronization history. It does not verify geological facts and does not promote DRAFT or REVIEW_REQUIRED scientific data to VERIFIED.

## Oil and gas field review

The review queue is driven exclusively by the backend-owned contract:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

The client displays `raw_payload`, `normalized_payload`, matching status, candidate entities and `entity_verification_status`.

Critical invariant: `ExternalEntityLink=VERIFIED` means the relationship to an external official record was reviewed. It **does not mean `GeologicalEntity=VERIFIED`**.

Available actions are delivered by the server as action descriptors:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

The desktop client does not maintain a duplicate rule table. It consumes `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, `method`, and `path`. Disabled actions are not sent. The server remains the final authority even when an action is enabled in the UI.

The desktop client does not submit a `reviewer` field. Reviewer identity is derived from the authenticated session on the server, preventing a client-supplied string from spoofing the reviewer.

## Geological study license review

The administrative license queue is read from:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Decisions use:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` means only that a normalized administrative license record was checked against its RAW/upstream payload. It does not create an `ExternalEntityLink`, does not create a `GeologicalEntity`, and does not publish a geological fact.

## Provenance and audit

Review screens show RAW and normalized payloads side by side so users can inspect source wording and GeoKZ’s internal normalized representation without losing provenance.

Master-data history is read through:

```text
GET /api/v1/audit/logs
GET /api/v1/audit/revisions/{resource_type}/{resource_id}
```

The full `AuditLog` is admin-only. Revision history is available to authenticated users for supported resource types: `source`, `geological_entity`, and `fact`.

Audit and revision history are append-only at the PostgreSQL layer. The desktop client has no API path that can overwrite or delete the history.

## Non-blocking UI

HTTP operations are executed through `QThreadPool/QRunnable` instead of blocking the Qt event loop. Network and HTTP API failures are shown explicitly to the user. A failed request never causes the client to invent a success state or locally mutate scientific data.

## Architecture boundary

```text
PySide6 widgets
    ↓
GeoKZApiClient (httpx)
    ↓ HTTPS/HTTP
FastAPI application/use cases
    ↓
domain + repositories
    ↓
PostgreSQL/PostGIS
```

The following path is prohibited:

```text
PySide6 → SQLAlchemy model → PostgreSQL
```

Direct database access would bypass RBAC, AuditLog, revision history, and backend-owned review contracts.

## Tests

Desktop API client unit tests verify that:

- bearer authorization is attached only after login;
- the token remains in memory;
- disabled actions are rejected without an HTTP request;
- required action fields are validated before dispatch;
- server-provided review paths are used without client reconstruction;
- RU/KK/EN desktop localization exposes the same key set;
- backend HTTP `detail` messages are preserved for error reporting.

The PostgreSQL/PostGIS integration test for `GET /api/v1/system/versions` verifies the actual Alembic head and bundled Core Dataset metadata.

## Current limitations

The first production-oriented desktop slice does not yet include the full map, cross-section renderer, offline cache, or Windows installer. It establishes the safe login/session, Data Sources, external review and provenance foundation. Later desktop slices can add Territory Explorer, Well Passport and the correlation viewer while preserving the same HTTP-only architecture and backend-owned contracts.
