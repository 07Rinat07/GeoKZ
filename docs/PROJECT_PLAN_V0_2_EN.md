# GeoKZ — Current Development Plan v0.3+

Status: `2026-09-05`, current feature slice `feature/core-dataset-manifest-importer-v0.3`.

## Purpose

GeoKZ is intended to be Kazakhstan's evidence-based geological working window: territory/coordinate → nearby fields, structures, wells and seismic → passports → depth intervals, lithology, reservoirs, logs, core and tests → neighboring-well correlation → primary sources, provenance, conflicts and expert review.

The application and user documentation are maintained in RU/KK/EN. External APIs enrich the local database but are not mandatory runtime dependencies and never silently overwrite verified master data.

## Implemented and merged to main

- FastAPI + PostgreSQL 17/PostGIS 3.5 + async SQLAlchemy + Alembic;
- real PostgreSQL/PostGIS CI through Alembic head;
- Territory Explorer, Geological Entity Passport and Well Passport;
- geographic/projected coordinate input, WGS84/UTM helper and persistent organization CRS registry;
- PostGIS nearby search;
- trajectory/log/test/core/seismic subsurface models;
- WellMarker and safe TVDSS/TVD/MD correlation;
- backend-owned visual cross-section view-model;
- isolated synthetic correlation workflow;
- official Kazakhstan Open Data connector and schema inspection;
- external scheduler + Update All;
- `kz-egov-oil-gas-fields` RAW → normalization → deterministic matching → human review;
- controlled vocabularies and subsurface canonical bindings while preserving RAW wording;
- correlation distance cartesian-product warning fix;
- `kz-egov-geological-study-licenses` (`zher_koinauyn_geologiyalyk_zer2/v6`) RAW → typed administrative normalization → record-level `REVIEW_REQUIRED → ACCEPTED/REJECTED` without unsupported entity matching;
- Alembic `20260905_0008` generic external-record reviewer metadata;
- license-review unit + PostgreSQL/PostGIS HTTP integration tests and RU/KK/EN documentation.

Latest merged main baseline: PR #11, merge SHA `f70675699aaae53b89eca23f29fefc61bdf78101`.

## Stable implemented API contracts

```text
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
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install
```

## Current P0 — GeoKZ Core Dataset manifest/importer

Goal: an independently versioned baseline shipped with the application but lifecycle-separated from Alembic schema migrations and external-provider sync versions.

Implemented in the current feature branch:

- Alembic `20260905_0009` and `CoreDatasetState` for installed dataset state;
- manifest schema v1 with `dataset_code`, `dataset_version`, `schema_version`, `created_at`, namespace, dependencies and per-file SHA-256;
- absolute/path-traversal protection;
- required-file and checksum validation before database writes;
- typed parser for sources, regions, entities and facts;
- duplicate `external_id` validation;
- `geokz-core:` namespace policy;
- bundle-internal reference validation;
- transactional upsert + rollback;
- manifest-SHA idempotence (`changed=false` on repeat import);
- bundled snapshot `2026.09.0-bootstrap`;
- deliberately minimal bootstrap: internal metadata source + Kazakhstan country-level navigation record without asserted boundary geometry and without invented geological entities/facts;
- REST status/install API;
- validate/install/status CLI;
- bundled Core Dataset version exposed in About;
- unit tests for checksum/path traversal/schema/duplicates/references;
- PostgreSQL/PostGIS integration tests for install/idempotence and rollback;
- dedicated `CORE_DATASET_RU/KK/EN.md` documentation.

API:

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=en
POST /api/v1/core-dataset/install?lang=en
```

CLI:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

For schema v1 the effective compatibility gate is `schema_version`. `minimum_app_version` remains informational metadata until a deliberate semantic-version policy is introduced; GeoKZ does not fake compatibility with an ad-hoc version comparator.

Current P0 merge gate: README + USER_GUIDE + roadmap + documentation policy in RU/KK/EN, final exact-head `compileall + Ruff + pytest`, PostgreSQL/PostGIS integration, then PR-CI on the same exact head and squash merge into `main`.

## Next P0 after merge

### 1. Authentication + AuditLog/Revision

- users/roles: expert/editor/admin;
- audit trail for review and scientific master-data changes;
- revision history for Fact/Entity/geometry/interpretation;
- verified data cannot be silently overwritten;
- administrative write APIs only behind authorization and audit.

### 2. Production PySide6 review/data-source screens

- Data Sources + Update All;
- separately display Application / DB schema / Core Dataset / provider versions;
- Core Dataset installed/update state;
- due/running/error/status;
- field review via server-owned action descriptors;
- license record ACCEPT/REJECT;
- provenance panel and contextual RU/KK/EN help.

### 3. Core Dataset update channel

After the safe local manifest/importer:

- signed bundle manifest;
- download/update channel;
- staging before activation;
- rollback to a previous installed snapshot;
- explicit app/schema/dataset compatibility policy;
- audit for every install/rollback.

### 4. Expand official Kazakhstan connectors

Add subsequent datasets through the common provider SDK only after current metadata/mapping/license/terms verification. Every source must include RAW, checksum/diff, typed normalizer, review rules and contract tests.

### 5. Global/open geology context

- USGS Mineral Resources;
- Macrostrat;
- OneGeology/OGC;
- Copernicus observation assets.

All external data preserves source/version/retrieved_at/license/attribution. Authority is not equivalent to truth: conflicting values remain parallel until expert resolution.

## Definition of Done for every slice

```text
feature branch
→ code + migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated feature docs RU/KK/EN when needed
→ exact-head CI green
→ PR
→ PR-CI green on the same head
→ squash merge into main
→ next task
```

The primary rule remains unchanged: GeoKZ works without external services; internet connectivity only enriches the local evidence-based database safely.
