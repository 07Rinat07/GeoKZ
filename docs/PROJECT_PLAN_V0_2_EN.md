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
- ✅ pyproj/PROJ `CoordinateResolver` and transformation to WGS84.
- ✅ `POST /api/v1/spatial/nearby` for nearby geological objects, wells and seismic surveys.
- ✅ HTTP integration test for `/api/v1/spatial/nearby` against a real PostGIS database.
- ✅ trajectory, well-log, test, core and seismic models.
- ✅ Well Correlation: markers, TVDSS preference, thickness/net pay, porosity/permeability, lithology/fluid/hydrocarbon differences.
- ✅ real PostGIS correlation integration test.
- ✅ synthetic demo dataset with 4 nearby wells, R1/R2 and J-II.
- ✅ Kazakhstan Open Data API v4 connector and external-integration foundation.
- ✅ RU/KK/EN user guides/roadmaps and documentation CI contract.

## Near-term P0
1. Connect coordinate-search results to nearby-well selection and correlation launch.
2. Add a Kazakhstan CRS catalog and configurable local organization CRS definitions.
3. Remove the SQLAlchemy warning in the correlation distance query.
4. Define the API data model for the visual cross-section viewer.
5. Build a demo workflow: coordinate → 4 wells → correlation.
6. External sync persistence + manual/scheduled sync.
7. Registry of official Kazakhstan Open Data datasets.
8. Core Dataset manifest/importer.
9. Controlled vocabularies + audit/revisions.

## Releases
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation.
- `v0.3`: coordinate/CRS hardening + correlation demo workflow.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: scheduled sync/matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
A user-facing feature is complete only when implementation, validation, tests, required migration, RU/KK/EN help/docs, provenance/verification rules and green CI are present.
