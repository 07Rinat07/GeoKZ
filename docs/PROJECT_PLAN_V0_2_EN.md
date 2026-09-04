# GeoKZ — Current Development Plan v0.2+

Status: `2026-09-04`, branch `feature/external-data-sync-v0.2`.

## Purpose
GeoKZ is a single working window for geology in Kazakhstan: territory/coordinate → fields and wells → full passport → lithology/stratigraphy/logs/core/tests/oil-gas-water → nearby-well correlation → source and evidence.

## Mandatory principles
- RU/KK/EN across all user-facing functionality and documentation.
- Verified data is never overwritten by external APIs or AI without review.
- RAW/source documents and LAS/DLIS/SEG-Y remain separate from interpretation.
- CRS, axis order, MD/TVD/TVDSS and units are always explicit.
- The Core Dataset remains usable offline.
- Demo/synthetic data is clearly marked and never presented as a production fact.

## Implemented
- ✅ FastAPI + PostgreSQL/PostGIS + Alembic.
- ✅ RU/KK/EN About/Help and author Sarmuldin Rinat / ura07srr@gmail.com.
- ✅ PostgreSQL/PostGIS CI: clean DB, migrations `0001 → 0004`, PostGIS/pg_trgm/unaccent and geography-distance checks.
- ✅ Territory Explorer, Geological Entity Passport and Well Passport.
- ✅ latitude/longitude and projected X/Y; dot/comma decimals; CRS; both X/Y axis orders.
- ✅ pyproj/PROJ `CoordinateResolver` and WGS84 transformation.
- ✅ `POST /api/v1/spatial/nearby` with a real PostGIS HTTP integration test.
- ✅ `GET /api/v1/spatial/crs-presets`: WGS84, UTM 38N–45N and RU/KK/EN warning; no silent CRS guessing.
- ✅ trajectory, well-log, test, core and seismic models.
- ✅ Well Correlation: markers, TVDSS, thickness/net pay, porosity/permeability, lithology/fluid/hydrocarbon differences.
- ✅ `POST /api/v1/correlation/wells` for a selected reference and neighboring wells; GET remains for compatibility.
- ✅ POST correlation is tested against a real PostGIS database.
- ✅ synthetic demo dataset with 4 nearby wells, R1/R2 and J-II.
- ✅ external-integration foundation: RAW/staging, checksum, SyncRun, source status and safe updates.
- ✅ generic Kazakhstan Open Data API v4 connector.
- ✅ official Kazakhstan Open Data registry: `stat_kgn_117/v10` (oil and gas fields) and `zher_koinauyn_geologiyalyk_zer2/v6` (geological-study licenses).
- ✅ official naming contract uses upstream `apiUri` + `version`; RAW field names are preserved while GeoKZ `code` and `record_type` remain separate internal identifiers.
- ✅ connector reads official `/meta/{apiUri}/{version}` and `/api/v4/mapping/{apiUri}/{version}` before ingestion.
- ✅ `GET /api/v1/integrations/kazakhstan/catalog` — catalog with `api_uri`, version and endpoint templates.
- ✅ `GET /api/v1/integrations/kazakhstan/{code}/schema` — upstream metadata/mapping inspection endpoint.
- ✅ `POST /api/v1/integrations/kazakhstan/register` — register the sources in the local GeoKZ database.
- ✅ `POST /api/v1/integrations/kazakhstan/{code}/sync` — manual REST synchronization into RAW/staging.
- ✅ `stat_kgn_117` normalizer extracts only the field name supported by the dataset and keeps RAW unchanged.
- ✅ oil/gas-field matching against `GeologicalEntity(object_type="field")` and `EntityName` aliases.
- ✅ exact/alias matches create only `ExternalEntityLink(status=REVIEW_REQUIRED)`; ambiguous/unmatched records remain in review; reviewer-set VERIFIED/REJECTED links are never overwritten automatically.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — normalize + match after RAW sync.
- ✅ sources are registered as `AUTOMATIC` with a 168-hour interval; the actual scheduler is still pending.
- ✅ the API key is read only from `GEOKZ_EGOV_API_KEY`; the local database remains usable without it.
- ✅ dedicated RU/KK/EN API-key acquisition and setup guides.
- ✅ dedicated RU/KK/EN Kazakhstan Open Data connection and resource-naming guides.
- ✅ README documents API-key setup, official `apiUri` contract, processing endpoint and resource onboarding rules.
- ✅ RU/KK/EN user guides/roadmaps and documentation CI contract.

## Near-term P0
1. API/view-model for the visual cross-section viewer: well columns, depth scale, markers, intervals and correlation lines.
2. Demo application workflow: coordinate → 4 nearby demo wells → selection → correlation section.
3. Persistent/configurable organization-local CRS definitions; SK-42/Gauss-Kruger only from confirmed EPSG/WKT/PROJ definitions.
4. Remove the SQLAlchemy cartesian-product warning in the correlation distance query.
5. Controlled vocabularies for lithology/markers/property kinds/units.
6. Scheduled external-source synchronization and an Update All workflow.
7. Review API/UI for confirming, rejecting and manually linking `ExternalEntityLink`, with creation of a new DRAFT field from an unmatched candidate only through an explicit user action.
8. Add more official Kazakhstan resources after metadata/mapping/license/data-quality review; the next candidate is the geological-study licenses resource.
9. Core Dataset manifest/importer.
10. Audit log/revisions.

## Releases
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + first official Kazakhstan REST integrations + safe oil/gas-field normalization/matching.
- `v0.3`: visual correlation data contract, CRS/local settings, complete demo workflow, scheduled external sync and review workflow.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: expanded external-source matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
A user-facing feature is complete only when implementation, validation, tests, required migration, RU/KK/EN help/docs, provenance/verification rules and green CI are present.
