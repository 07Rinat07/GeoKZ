# GeoKZ — Current Development Plan v0.3+

Status: `2026-09-05`, current feature slice `feature/geological-study-license-review-v0.3`.

## Purpose
GeoKZ is being built as an evidence-based geological workspace for Kazakhstan: territory/coordinate → nearby fields, structures, wells and seismic → passports → lithology, reservoirs, logs, core, tests, oil/gas/water → neighboring-well correlation → primary sources, provenance, conflicts and expert review.

The user-facing product and documentation are maintained in RU/KK/EN. External APIs enrich the local database but are not mandatory runtime dependencies and never overwrite verified master data automatically.

## Implemented and merged into main

- FastAPI + PostgreSQL/PostGIS + async SQLAlchemy + Alembic;
- real PostgreSQL/PostGIS CI with migration-to-head gate;
- territory explorer, Geological Entity Passport and Well Passport;
- geographic/projected X/Y input, dot/comma parsing, WGS84/UTM helper;
- confirmed persistent organization-local CRS registry using EPSG/WKT/PROJ;
- PostGIS nearby search;
- trajectory, logs, tests, core and 2D/3D seismic subsurface models;
- WellMarker and depth-safe TVDSS/TVD/MD correlation;
- visual cross-section endpoint: `POST /api/v1/correlation/wells/view`;
- synthetic end-to-end demo: `POST /api/v1/correlation/demo/workflow`;
- official Kazakhstan Open Data connector with metadata/mapping/schema inspection;
- Update All: `POST /api/v1/integrations/sync-all`;
- scheduler status: `GET /api/v1/integrations/scheduler/status`;
- run due: `POST /api/v1/integrations/scheduler/run-due`;
- oil/gas field processing: `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process`;
- field review: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`;
- localized field-review view: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`;
- persistent controlled vocabularies (`lithology`, `marker_type`, `property_kind`, `unit`) plus canonical bindings to subsurface records while preserving RAW/source wording;
- correlation distance-query cartesian-product warning removed and protected by a PostGIS regression test.

## Current P0 — geological study license register

```text
GeoKZ code:  kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

Implemented in the current feature branch:

- administrative license normalizer;
- immutable `raw_payload` preservation;
- normalized `license_number`, `issue_date`, type/scope, term, basis, authority, holder and BIN;
- Alembic `20260905_0008` with generic record-review metadata: `reviewed_by`, `reviewed_at`, `review_comment`;
- record-level `REVIEW_REQUIRED → ACCEPTED/REJECTED`;
- no automatic `ExternalEntityLink`, because the verified v6 dataset card does not expose a stable geological-object/geometry identifier;
- upstream `CHANGED` invalidates the old human review decision;
- unit and PostgreSQL/PostGIS HTTP integration tests;
- dedicated RU/KK/EN documentation.

API:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

Merge gate: final exact-head Python quality and PostgreSQL/PostGIS integration must both be green, followed by green PR-CI on the same head, then squash merge to `main`.

## Next P0 after merge

### 1. GeoKZ Core Dataset manifest/importer

- versioned `manifest.json`;
- dataset/schema version, created_at and SHA-256;
- transactional import/update with rollback;
- baseline entities/sources/facts/regions/vocabularies;
- Core Dataset version exposed in About/Data Sources;
- checksum validation and preparation for digital signatures;
- tests for repeated import, incompatible schema and rollback.

### 2. Authentication + AuditLog/Revision

- expert/editor/admin roles;
- audit trail for review and scientific master-data changes;
- Fact/Entity/geometry/interpretation revision history;
- verified data cannot be silently overwritten;
- controlled-vocabulary write API only after roles/audit exist.

### 3. Production PySide6 review/data-source screens

- Data Sources + Update All;
- scheduler due/running/error/version state;
- field review driven by server-owned action descriptors;
- license ACCEPT/REJECT queue;
- provenance panel and RU/KK/EN contextual help.

### 4. More official Kazakhstan geology datasets

Each new source is onboarded only after current metadata/mapping/license/terms verification. Reuse the provider SDK, RAW + checksum/diff, typed normalizer, review rules and contract tests instead of duplicating bespoke business logic for every dataset.

### 5. Global/open geology context

After the official Kazakhstan integration layer is stable:

- USGS Mineral Resources;
- Macrostrat;
- OneGeology/OGC;
- Copernicus observation assets.

Every external record preserves source/version/retrieved_at/license/attribution. Authority is not equivalent to truth: conflicting values remain traceable and are resolved by expert review.

## Definition of Done

```text
feature branch
→ code + migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated RU/KK/EN feature docs when needed
→ exact-head CI green
→ PR
→ PR-CI green on the same head
→ squash merge into main
→ next roadmap item
```

Core rule: GeoKZ must remain usable without external services; internet access safely enriches its local evidence-based database.
