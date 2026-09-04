# GeoKZ — Current Development Plan v0.2+

Document status: `2026-09-04`, branch `feature/external-data-sync-v0.2`.

Legend: `✅` implemented in code; `🧪` implemented/partially implemented and awaiting CI or integration validation; `⬜` planned.

## 1. Product purpose
GeoKZ is a single working window for geological information about Kazakhstan. A user selects a territory, coordinate, field/deposit, geological structure or well and receives the most complete available information from the embedded GeoKZ Core database and permitted external sources.

Primary workflow:

```text
Territory / coordinate
  ↓
fields / structures / wells / seismic / maps
  ↓
geological object passport
  ↓
well passport
  ↓
trajectory / intervals / lithology / logs / core / tests / oil-gas-water
  ↓
cross-well section correlation
  ↓
source / document / file / page / evidence
```

## 2. Mandatory principles
- RU/KK/EN across all user-facing functionality;
- documentation is part of Definition of Done;
- important data carries provenance and verification status;
- RAW/source material is not replaced by interpretation;
- external APIs and AI never silently overwrite verified master data;
- Core Dataset remains usable offline;
- CRS and MD/TVD/TVDSS references are explicit;
- measurements preserve units and reference systems.

## 3. Main domains
- Territory / Spatial: regions, coordinates, X/Y, CRS, nearby-object search;
- Field / Geological Object: geology, tectonics, stratigraphy, lithology, reservoirs, oil/gas/water;
- Well / Wellbore: passport, trajectory, intervals, logs, core and tests;
- Well Correlation: markers, reservoirs, visual and textual section comparison;
- Seismic / Geophysics: 2D/3D, lines/volumes and SEG-Y catalog;
- Documents / Evidence: source/document/page/fact/evidence/conflict;
- Integrations: RAW staging, checksum/diff, matching, review and synchronization.

## 4. Current status

### Platform
- ✅ FastAPI/PostGIS foundation;
- ✅ Evidence model;
- ✅ About API in RU/KK/EN;
- ✅ contextual Help API in RU/KK/EN;
- 🧪 full CI must be rerun after the latest changes.

### External data
- ✅ ExternalDataSource/Record/SyncRun/EntityLink;
- ✅ ExternalDataConnector;
- ✅ Kazakhstan Open Data API v4 connector;
- ⬜ persistence/manual/scheduled synchronization;
- ⬜ official dataset registry;
- ⬜ USGS/Macrostrat/OGC connectors.

### Spatial
- ✅ Territory Explorer and Geological Entity Passport;
- ✅ PostGIS nearby-search service;
- ✅ coordinate models accepting dot/comma decimals;
- ✅ projected X/Y + CRS + axis order;
- 🧪 complete coordinate HTTP workflow;
- ⬜ PROJ/pyproj transformation and Kazakhstan/local CRS presets.

### Subsurface
- ✅ trajectory, well-log, test, core and seismic models;
- ✅ Well Passport API;
- 🧪 migration/integration validation;
- ⬜ LAS/DLIS/WITSML and SEG-Y import.

### Well Correlation
- ✅ WellMarker model and migration 0004;
- ✅ correlation API contract/service;
- ✅ TVDSS-preferred comparison;
- ✅ marker-depth deltas and protection against incompatible depth references;
- ✅ `/api/v1/correlation/wells/{reference_well_id}`;
- ⬜ reservoir-thickness comparison;
- ⬜ log-curve-assisted correlation;
- ⬜ PySide6 cross-section viewer.

### Documentation
- ✅ RU/KK/EN user guides;
- ✅ Documentation Policy;
- ✅ I18N and Business Domain docs;
- ✅ RU master roadmap plus KK/EN roadmap translations;
- ⬜ CI documentation contract.

## 5. Near-term P0 backlog
1. Full Ruff/pytest/CI run.
2. PostgreSQL/PostGIS integration tests and migrate-to-head test.
3. Coordinate-search HTTP endpoint.
4. PROJ/pyproj CRS transformation.
5. External-sync persistence/manual endpoint.
6. Kazakhstan Open Data dataset registry.
7. Correlation integration tests and demo markers.
8. Reservoir-thickness/fluid difference comparison.
9. RU/KK/EN documentation CI contract.
10. Core Dataset manifest and controlled vocabularies.

## 6. Release plan
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation;
- `v0.3`: CRS, spatial/subsurface hardening and correlation engine;
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y files;
- `v0.5`: scheduled sync, matching, review/audit;
- `v0.6`: unified RU/KK/EN search;
- `v0.7`: GIS/PySide6 visualization and correlation viewer;
- `v0.8`: geological model hardening;
- `v0.9`: AI candidates with human review;
- `v1.0`: production GeoKZ Desktop.

## 7. User-feature Definition of Done
A user-facing feature is complete only when it has API/domain implementation, validation, tests, required migration, RU/KK/EN contextual help, all three user guides, all three roadmap variants, applicable provenance rules and green CI.
