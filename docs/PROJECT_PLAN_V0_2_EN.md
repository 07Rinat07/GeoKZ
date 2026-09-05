# GeoKZ — Current Development Plan v0.3+

Status: `2026-09-05`. Current feature slice: `feature/pyside6-data-review-client-v0.3`.

## Goal

GeoKZ is an evidence-based geological workspace for Kazakhstan: territory/coordinate → objects/fields/wells/seismic → passports → subsurface data → correlation → sources/provenance → expert review.

The core system works without external services. Online sources enrich the local database but never silently overwrite verified master data.

## Already merged into main

- FastAPI + PostgreSQL 17/PostGIS 3.5 + async SQLAlchemy + Alembic;
- Territory Explorer, Geological Entity Passport and Well Passport;
- WGS84/projected X/Y, UTM 38N–45N and organization-local CRS registry;
- PostGIS nearby search;
- trajectory, logs, tests, core, seismic and markers;
- safe well correlation and visual cross-section view-model;
- synthetic demo correlation workflow;
- Kazakhstan Open Data connector + schema inspection;
- external scheduler + Update All;
- oil/gas field normalization/matching/review;
- geological study license normalization + record-level review;
- controlled geological vocabularies;
- independently versioned Core Dataset manifest/importer;
- authentication + RBAC + server-owned reviewer identity;
- append-only `AuditLog` + `MasterDataRevision`;
- Alembic head `20260905_0010`;
- PR #13 was squash-merged into `main` as `5d605a3f034343f3349e1fcf1c0b35aa4a153e2d` after green Python and PostgreSQL/PostGIS CI.

## Stable backend contracts

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
POST /api/v1/correlation/wells/view
POST /api/v1/correlation/demo/workflow
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
GET  /api/v1/audit/logs
GET  /api/v1/audit/revisions/{resource_type}/{resource_id}
```

## Current P0 — Production PySide6 review/data-source client

Goal: the first production-oriented desktop layer with no direct ORM/database access.

The current feature slice implements:

- HTTP-only `GeoKZApiClient`;
- bearer token stored only in process memory;
- login/logout and current role display;
- non-blocking PySide6 shell through `QThreadPool/QRunnable`;
- Data Sources + Update All;
- independent version contract:

```text
GET /api/v1/system/versions
```

- Application / Alembic DB schema / bundled Core Dataset / installed Core Dataset / provider versions;
- due/running/error/last-success source state;
- field review driven only by server-owned action descriptors;
- license record ACCEPT/REJECT;
- RAW + normalized provenance;
- AuditLog/revision viewer;
- contextual help in RU/KK/EN;
- `geokz-desktop` entry point;
- unit tests for the desktop API client/localization;
- PostgreSQL/PostGIS integration test for the system version contract;
- `DESKTOP_CLIENT_RU/KK/EN.md`.

### Desktop invariants

- PySide6 never imports SQLAlchemy models;
- the UI does not duplicate `CONFIRM_LINK/REJECT_LINK/MANUAL_LINK/CREATE_DRAFT_FIELD` business rules;
- reviewer identity comes from the authenticated session;
- `ExternalEntityLink=VERIFIED` does not make `GeologicalEntity=VERIFIED`;
- token/password are not persisted to files/logs/settings;
- a network failure never creates a local scientific “success” state.

### Merge gate

```text
compileall
→ Ruff
→ unit tests
→ PostgreSQL/PostGIS integration
→ README
→ USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ DESKTOP_CLIENT RU/KK/EN
→ exact-head CI green
→ PR
→ PR-CI green on the same SHA
→ squash merge to main
```

## Next P0 after desktop merge — Core Dataset update channel

1. Signed manifest/bundle format and verification policy.
2. HTTP download/update channel with no arbitrary filesystem import.
3. Download → checksum/signature verify → staging → transactional activation.
4. Preserve the previous installed snapshot for rollback.
5. Explicit application/Alembic/Core Dataset compatibility policy.
6. Audit every install/update/rollback with an authenticated actor.
7. Refuse activation when signature/checksum/compatibility is not confirmed.
8. RU/KK/EN UI state for available/current/failed/rollback.

## Later directions

- new official Kazakhstan connectors only after metadata/mapping/license/terms verification;
- USGS Mineral Resources, Macrostrat, OneGeology/OGC and Copernicus context;
- Territory Explorer/map desktop screen;
- Geological Entity Passport;
- Well Passport;
- visual correlation renderer;
- document/evidence viewer;
- later, a read-only offline cache.

## Definition of Done

```text
feature branch
→ code + migrations/contracts
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated docs RU/KK/EN
→ exact-head CI green
→ PR
→ PR-CI green on the same exact head
→ squash merge to main
→ next task
```

Author: **Sarmuldin Rinat — ura07srr@gmail.com**.
