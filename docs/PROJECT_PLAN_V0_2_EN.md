# GeoKZ — Current Development Plan v0.2+

Status: `2026-09-04`, branch `feature/local-crs-registry-v0.3`.

## Purpose
GeoKZ is an evidence-first geological information system for Kazakhstan: territory/coordinate → object → well → intervals/logs/core/tests → correlation → source and evidence.

## Mandatory principles
- RU/KK/EN for all user-facing features and documentation.
- Verified master data is never changed by external APIs or AI without review.
- RAW/source documents remain separate from interpretation.
- CRS, axis order, MD/TVD/TVDSS and units are explicit.
- The Core Dataset works without mandatory internet access.
- Synthetic/demo data stays separate from production data.
- UI clients do not duplicate backend business rules.
- Periodic external synchronization runs as a dedicated process/service.

## Implemented
- ✅ FastAPI + PostgreSQL/PostGIS + async SQLAlchemy + Alembic.
- ✅ PostgreSQL/PostGIS CI with migrations, PostGIS, pg_trgm and unaccent.
- ✅ Territory Explorer, Geological Entity Passport and Well Passport.
- ✅ geographic/projected coordinate input, WGS84/UTM helper and pyproj/PROJ resolution.
- ✅ `POST /api/v1/spatial/nearby` with a real PostGIS integration test.
- ✅ trajectory, well logs, tests, core, seismic and Well Correlation.
- ✅ `POST /api/v1/correlation/wells` and backend-owned `POST /api/v1/correlation/wells/view`.
- ✅ safe visual cross-section contract: `TVDSS → TVD → MD`, renderability, MARKER/HORIZON lines and warnings.
- ✅ synthetic demo dataset and complete `POST /api/v1/correlation/demo/workflow` from coordinate to cross-section.
- ✅ external RAW/staging, checksum, SyncRun and ExternalEntityLink foundation.
- ✅ Kazakhstan Open Data API v4 connector with `stat_kgn_117/v10` and `zher_koinauyn_geologiyalyk_zer2/v6` registry.
- ✅ oil/gas-field normalization, safe matching, review queue/actions and RU/KK/EN review UI contract.
- ✅ dedicated external sync scheduler, due/retry policy, row-lock protection and Update All.
- ✅ persistent organization/local CRS registry: `organization_crs_definitions`, migration `20260904_0005`.
- ✅ local CRS entries accept exact `EPSG`, `WKT`, or `PROJ`, and store canonical WKT plus `source_reference`.
- ✅ explicit confirmation workflow; only active + `is_confirmed=true` entries resolve through `registered_crs_code`.
- ✅ changing the definition, axis order, or source reference automatically clears confirmation.
- ✅ spatial nearby and demo correlation use registry-aware coordinate resolution; unconfirmed CRS entries are blocked.
- ✅ local CRS registry has unit coverage and a real PostgreSQL/PostGIS API integration test.
- ✅ dedicated `LOCAL_CRS_REGISTRY_*` documentation exists in RU/KK/EN.

## Near-term P0
1. Remove the remaining SQLAlchemy cartesian-product warning in the correlation distance query without changing PostGIS distance results.
2. Add controlled vocabularies for lithology/markers/property kinds/units.
3. Add normalizer/review for the geological-study licenses resource after mapping/license/data-quality validation.
4. Add the Core Dataset manifest/importer.
5. Add Authentication + AuditLog/revisions for review, CRS confirmation, and master-data changes.
6. Build the production PySide6 external-review screen on the stable backend view-model contract.
7. Expand to USGS/Macrostrat/OneGeology only after license and contract validation.

## Releases
- `v0.2`: platform/evidence/integration/spatial/subsurface/correlation foundation and first Kazakhstan Open Data integrations — merged to `main`.
- `v0.3`: review UI, scheduled sync, visual cross-section, complete demo workflow, and persistent local CRS registry.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y import.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + production visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
A user-facing feature is complete only with implementation, validation, tests, required migration, RU/KK/EN docs/help, provenance/verification rules, and green CI.
