# GeoKZ — Current Development Plan v0.2+

Status: `2026-09-04`, branch `feature/external-data-sync-v0.2`.

## Purpose
GeoKZ is a single working window for geology in Kazakhstan: territory/coordinate → fields and wells → full passport → lithology/stratigraphy/logs/core/tests/oil-gas-water → nearby-well correlation → source and evidence.

## Mandatory principles
- RU/KK/EN across all user-facing functionality and documentation.
- Verified data is never overwritten by external APIs or AI without review.
- RAW/source documents remain separate from interpretation.
- CRS, axis order, MD/TVD/TVDSS and units are explicit.
- The Core Dataset remains usable offline.
- Demo/synthetic data is clearly marked.

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
- ✅ automatic exact/alias candidates remain `REVIEW_REQUIRED`; ambiguous/unmatched records remain available for expert review; reviewer decisions survive reprocessing.
- ✅ review queue: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ review actions: confirm/reject candidate, manual linking to an existing field, and explicit creation of a new field only from `UNMATCHED`.
- ✅ a field created from an external record always starts with `verification_status=DRAFT`; a verified source association never makes the geological object VERIFIED automatically.
- ✅ reviewer identity/comment are stored on `ExternalEntityLink`; full authentication and AuditLog are still planned.
- ✅ trilingual documentation for external integration, resource naming and field review, enforced by CI.

## Near-term P0
1. Bring the review backend to fully green PostgreSQL/PostGIS CI and define the review-queue UI contract.
2. Scheduled external synchronization and Update All.
3. Visual cross-section viewer API/view-model and complete demo workflow.
4. Persistent/configurable organization-local CRS definitions.
5. Remove the remaining SQLAlchemy cartesian-product warning in correlation distance queries.
6. Controlled vocabularies for lithology/markers/property kinds/units.
7. Add normalization/review for the geological-study licenses resource after mapping/license/data-quality validation.
8. Core Dataset manifest/importer.
9. Authentication + AuditLog/revisions.
10. Production PySide6 review/integration UI.

## Releases
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + first Kazakhstan REST integrations + safe oil/gas-field normalization/matching/review.
- `v0.3`: visual correlation contract, CRS/local settings, complete demo workflow, scheduled sync and review UI.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
A user-facing feature is complete only when implementation, validation, tests, required migration, RU/KK/EN help/docs, provenance/verification rules and green CI are present.
