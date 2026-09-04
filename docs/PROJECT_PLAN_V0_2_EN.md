# GeoKZ — Current Development Plan v0.2+

Document status: `2026-09-04`, branch `feature/external-data-sync-v0.2`.

Legend: `✅` implemented; `🧪` awaiting CI/integration validation; `⬜` planned.

## 1. Product purpose
GeoKZ is a single working window for geology in Kazakhstan: territory/coordinate → geological object → well → intervals/logs/core/tests → cross-well correlation → source/evidence.

## 2. Mandatory principles
- RU/KK/EN across all user-facing functionality;
- documentation is part of Definition of Done;
- provenance and verification status for important data;
- RAW/source material is not replaced by interpretation;
- external APIs/AI never silently overwrite verified master data;
- Core Dataset remains usable offline;
- CRS and MD/TVD/TVDSS are explicit;
- measurements preserve units/reference systems.

## 3. Main domains
- Territory / Spatial: regions, coordinates, X/Y, CRS, nearby objects;
- Field / Geological Object: geology, tectonics, stratigraphy, lithology, reservoirs, oil/gas/water;
- Well / Wellbore: passport, trajectory, intervals, logs, core, tests;
- Well Correlation: markers, reservoirs, visual/textual section comparison;
- Seismic / Geophysics: 2D/3D, lines/volumes, SEG-Y;
- Documents / Evidence and Integrations.

## 4. Current status

### Platform
- ✅ FastAPI/PostGIS, Evidence, About RU/KK/EN, Help RU/KK/EN;
- 🧪 full CI rerun required after the latest changes.

### External data
- ✅ ExternalDataSource/Record/SyncRun/EntityLink;
- ✅ ExternalDataConnector and Kazakhstan Open Data API v4 connector;
- ⬜ persistence/manual/scheduled sync and additional connectors.

### Spatial
- ✅ Territory Explorer / Geological Entity Passport;
- ✅ PostGIS nearby search;
- ✅ dot/comma coordinate models;
- ✅ projected X/Y + CRS + axis order;
- 🧪 complete HTTP coordinate workflow;
- ⬜ PROJ/pyproj and Kazakhstan/local CRS presets.

### Subsurface
- ✅ trajectory, well-log, test, core and seismic models;
- ✅ Well Passport API;
- 🧪 migration/integration validation;
- ⬜ LAS/DLIS/WITSML and SEG-Y import.

### Well Correlation
- ✅ WellMarker + migration 0004;
- ✅ correlation API/service;
- ✅ TVDSS-preferred marker comparison and depth-reference safety;
- ✅ marker-depth deltas;
- ✅ same-local-horizon matching;
- ✅ thickness and net-pay deltas;
- ✅ porosity/permeability, lithology, fluid and hydrocarbon-status differences;
- 🧪 CI/PostGIS integration tests;
- ⬜ log-curve-assisted correlation;
- ⬜ PySide6 cross-section viewer.

### Documentation
- ✅ RU/KK/EN user guides;
- ✅ RU/KK/EN roadmaps;
- ✅ Documentation Policy;
- ✅ CI documentation-contract test.

## 5. Near-term P0 backlog
1. Full Ruff/pytest/CI.
2. PostgreSQL/PostGIS integration and migrate-to-head test.
3. Coordinate-search HTTP endpoint and PROJ/pyproj.
4. External-sync persistence/manual endpoint.
5. Kazakhstan Open Data dataset registry.
6. Correlation integration tests and demo markers/intervals.
7. Unit tests for marker/reservoir comparison.
8. Core Dataset manifest and controlled vocabularies.
9. Audit/revisions.
10. PySide6 correlation-viewer data-model prototype.

## 6. Release plan
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation;
- `v0.3`: CRS + correlation hardening;
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y;
- `v0.5`: scheduled sync/matching/review;
- `v0.6`: unified RU/KK/EN search;
- `v0.7`: GIS/PySide6 + correlation viewer;
- `v1.0`: production GeoKZ Desktop.

## 7. Definition of Done
A user-facing feature is complete only when implementation, validation, tests, required migration, RU/KK/EN help, all three user guides, all three roadmaps, provenance rules and green CI are present.
