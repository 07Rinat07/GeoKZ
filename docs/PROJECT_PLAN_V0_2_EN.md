# GeoKZ — Current Development Plan v0.2+

Status: `2026-09-04`, branch `feature/demo-correlation-workflow-v0.3`. The v0.2 foundation, review UI contract, dedicated external-sync scheduler, and visual cross-section view-model have already been merged into `main` after green CI.

## Purpose
GeoKZ is a single working window for geology in Kazakhstan: territory/coordinate → fields and wells → full passport → lithology/stratigraphy/logs/core/tests/oil-gas-water → nearby-well correlation → source and evidence.

## Mandatory principles
- RU/KK/EN across all user-facing functionality and documentation.
- Verified data is never overwritten by external APIs or AI without review.
- RAW/source documents remain separate from interpretation.
- CRS, axis order, MD/TVD/TVDSS and units are explicit.
- The Core Dataset remains usable offline.
- Demo/synthetic data is clearly marked and is never production evidence.
- UI clients do not duplicate backend business rules or depth/correlation logic.
- Periodic external synchronization runs as a dedicated process/service.

## Implemented
- ✅ FastAPI + PostgreSQL/PostGIS + Alembic and PostgreSQL/PostGIS CI.
- ✅ Territory Explorer, Geological Entity Passport, Well Passport.
- ✅ coordinate resolver, CRS helper and `POST /api/v1/spatial/nearby`.
- ✅ trajectory, well logs, tests, core, seismic and Well Correlation.
- ✅ Kazakhstan Open Data API v4 connector, RAW/staging, checksum/diff, resource registry and review workflow.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process`.
- ✅ `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` with backend-owned action descriptors.
- ✅ manual Update All: `POST /api/v1/integrations/sync-all`.
- ✅ scheduled dispatch: `POST /api/v1/integrations/scheduler/run-due`; status: `GET /api/v1/integrations/scheduler/status`.
- ✅ dedicated external scheduler plus PostgreSQL parallel-run/stale-run protection.
- ✅ backend-owned visual cross-section: `POST /api/v1/correlation/wells/view`.
- ✅ common depth axis uses `TVDSS → TVD → MD`; incompatible items return `renderable=false`.
- ✅ ready-to-render `MARKER`/`HORIZON` line segments and stable warning codes.
- ✅ complete synthetic demo workflow: `POST /api/v1/correlation/demo/workflow`.
- ✅ the first call resolves the coordinate, performs a PostGIS discovery and returns `stage=DISCOVERY`, `nearby_demo_wells`, a suggested reference and a selection contract.
- ✅ the second call with `reference_well_id` and `well_ids` returns `stage=CROSS_SECTION_READY` and the backend-owned `cross_section`.
- ✅ demo selection is restricted to `synthetic-correlation-demo-v1`; an ordinary production well at the same location is excluded.
- ✅ incomplete, duplicate, reference-in-compared and out-of-discovery selections are rejected with HTTP `422`.
- ✅ the demo dataset identifier is shared between runtime workflow and `python -m scripts.seed_correlation_demo`.
- ✅ the complete demo HTTP path is covered by a real PostgreSQL/PostGIS integration test that also creates a nearby production fixture well.
- ✅ README, user guides, roadmaps and feature contracts are maintained in RU/KK/EN and enforced by documentation CI.

## Near-term P0
1. Persistent/configurable organization-local CRS definitions; SK-42/Gauss-Kruger only from confirmed EPSG/WKT/PROJ definitions.
2. Remove the remaining SQLAlchemy cartesian-product warning in correlation distance queries without changing PostGIS distance results.
3. Controlled vocabularies for lithology/markers/property kinds/units.
4. Add normalization/review for the geological-study licenses resource after mapping/license/data-quality validation.
5. Core Dataset manifest/importer.
6. Authentication + AuditLog/revisions for review and master-data changes.
7. Production PySide6 external-review screen on top of the stable backend view-model contract.
8. Expand the provider registry to USGS/Macrostrat/OneGeology only after separate license and contract validation.

## Releases
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation and first Kazakhstan integrations.
- `v0.3`: review UI contract, scheduled external sync/Update All, visual correlation contract, complete synthetic demo workflow and CRS/local settings.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
A user-facing feature is complete only when implementation, validation, tests, required migration, RU/KK/EN help/docs, provenance/verification rules and green CI are present.
