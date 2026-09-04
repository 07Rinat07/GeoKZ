# GeoKZ — Current Development Plan v0.2+

Status: `2026-09-04`, branch `feature/external-sync-scheduler-v0.3`. The v0.2 foundation and review UI contract have already been merged into `main` after green CI.

## Purpose
GeoKZ is a single working window for geology in Kazakhstan: territory/coordinate → fields and wells → full passport → lithology/stratigraphy/logs/core/tests/oil-gas-water → nearby-well correlation → source and evidence.

## Mandatory principles
- RU/KK/EN across all user-facing functionality and documentation.
- Verified data is never overwritten by external APIs or AI without review.
- RAW/source documents remain separate from interpretation.
- CRS, axis order, MD/TVD/TVDSS and units are explicit.
- The Core Dataset remains usable offline.
- Demo/synthetic data is clearly marked.
- UI clients do not duplicate backend business rules: review action availability and form requirements come from the backend view-model.
- Periodic external synchronization runs as a dedicated process/service, not as a background loop inside every FastAPI worker.

## Implemented
- ✅ FastAPI + PostgreSQL/PostGIS + Alembic.
- ✅ RU/KK/EN About/Help and author Sarmuldin Rinat / ura07srr@gmail.com.
- ✅ PostgreSQL/PostGIS integration CI, spatial search, CRS helper, object and well passports.
- ✅ trajectory, well-log, test, core, seismic and Well Correlation models/workflows.
- ✅ Kazakhstan Open Data API v4 connector with official `apiUri` + `version`, metadata/mapping inspection, RAW staging and checksum/diff.
- ✅ official registry for `stat_kgn_117/v10` and `zher_koinauyn_geologiyalyk_zer2/v6`.
- ✅ catalog/register/schema/sync REST endpoints.
- ✅ `stat_kgn_117` normalizer and matching against `GeologicalEntity(object_type="field")` and `EntityName` aliases.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — normalize + match after RAW sync.
- ✅ automatic exact/alias candidates remain `REVIEW_REQUIRED`; ambiguous/unmatched records remain available for expert review.
- ✅ repeated `process` is idempotent for unresolved automatic links and does not create duplicate `ExternalEntityLink` pairs.
- ✅ reviewer-locked decisions (`VERIFIED`, `REJECTED`, `MANUAL`, reviewer/comment) survive reprocessing.
- ✅ technical review queue: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ review actions: confirm/reject candidate, manual linking to an existing field, and explicit creation of a new field only from `UNMATCHED`.
- ✅ a field created from an external record always starts with `verification_status=DRAFT`; a verified source association never makes the geological object VERIFIED automatically.
- ✅ reviewer identity/comment are stored on `ExternalEntityLink`; full authentication and AuditLog are still planned.
- ✅ review/matching backend was validated by green `Python quality checks` and PostgreSQL/PostGIS integration tests and merged to `main`.
- ✅ review queue UI/view-model contract: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`.
- ✅ the view-model exposes RU/KK/EN title/policy note, `total_pending`, pagination, localized candidate names, separate `entity_verification_status`, and stable `matching_status` values.
- ✅ action descriptors `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, and `CREATE_DRAFT_FIELD` expose `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, and the exact backend `path`.
- ✅ `UNKNOWN` matching status is a forward-compatible client fallback.
- ✅ review view-model has unit coverage and a real PostgreSQL HTTP integration test.
- ✅ periodic external synchronization runs in the dedicated `python -m scripts.external_sync_scheduler` process/service.
- ✅ manual Update All: `POST /api/v1/integrations/sync-all`, with independent per-source results and batch continuation after a provider failure.
- ✅ scheduled due dispatch: `POST /api/v1/integrations/scheduler/run-due`; status endpoint: `GET /api/v1/integrations/scheduler/status`.
- ✅ due/retry timing is derived from `sync_interval_hours`, `last_success_at`, and the latest error; a new `AUTOMATIC` source is due immediately.
- ✅ PostgreSQL `SELECT ... FOR UPDATE` serializes sync-run reservation while the external HTTP transfer runs after the row lock has been released.
- ✅ a second concurrent run returns `ALREADY_RUNNING`; stale `RUNNING` rows are converted to `FAILED` after a configurable timeout.
- ✅ Docker Compose runs a separate `geokz-external-sync-scheduler`; FastAPI workers contain no scheduler loop.
- ✅ scheduler policy has unit tests plus real PostgreSQL active-run/stale-run integration coverage.
- ✅ API credentials remain only in `GEOKZ_EGOV_API_KEY`; without the key, the local GeoKZ database continues to work and provider failures remain isolated to the source.
- ✅ trilingual documentation covers external integration, field review, review UI contract, and external synchronization scheduler behavior, enforced by CI.

## Near-term P0
1. Visual cross-section viewer API/view-model: well columns, depth scale, markers, intervals and correlation lines.
2. Coordinate → nearby demo wells → selection → correlation section end-to-end flow.
3. Persistent/configurable organization-local CRS definitions; SK-42/Gauss-Kruger only from confirmed EPSG/WKT/PROJ definitions.
4. Remove the remaining SQLAlchemy cartesian-product warning in correlation distance queries without changing PostGIS distance results.
5. Controlled vocabularies for lithology/markers/property kinds/units.
6. Add normalization/review for the geological-study licenses resource after mapping/license/data-quality validation.
7. Core Dataset manifest/importer.
8. Authentication + AuditLog/revisions for review and master-data changes.
9. Production PySide6 external-review screen on top of the stable backend view-model contract.
10. Expand the scheduler provider registry to USGS/Macrostrat/OneGeology only after separate license and contract validation.

## Releases
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + first Kazakhstan REST integrations + safe oil/gas-field normalization/matching/review — merged to `main`.
- `v0.3`: review UI contract, dedicated scheduled external sync/Update All, visual correlation contract, CRS/local settings and complete demo workflow.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
A user-facing feature is complete only when implementation, validation, tests, required migration, RU/KK/EN help/docs, provenance/verification rules and green CI are present.
