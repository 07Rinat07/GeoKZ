# GeoKZ — v0.2+ өзекті даму жоспары

Құжат мәртебесі: `2026-09-04`, тармақ `feature/external-data-sync-v0.2`.

Белгілер: `✅` кодта іске асырылған; `🧪` CI/интеграциялық тексеру қажет; `⬜` жоспарланған.

## 1. Өнімнің мақсаты
GeoKZ — Қазақстан геологиясы бойынша бірыңғай жұмыс терезесі: аумақ/координата → объект → ұңғыма → интервал/ҰГЗ/керн/сынақ → көршілес ұңғымалар корреляциясы → дереккөз/дәлел.

## 2. Міндетті қағидалар
- RU/KK/EN барлық пайдаланушы функцияларында;
- құжаттама Definition of Done бөлігі;
- provenance және verification status;
- RAW/бастапқы материал интерпретациямен алмастырылмайды;
- verified master data сыртқы API/AI арқылы автоматты өзгермейді;
- Core Dataset интернетсіз жұмыс істейді;
- CRS және MD/TVD/TVDSS анық көрсетіледі;
- measurements units/reference system сақтайды.

## 3. Негізгі домендер
- Territory / Spatial: аймақ, координаталар, X/Y, CRS, жақын объектілер;
- Field / Geological Object: геология, тектоника, стратиграфия, литология, коллекторлар, мұнай/газ/су;
- Well / Wellbore: паспорт, траектория, интервалдар, ҰГЗ, керн, сынақтар;
- Well Correlation: реперлер, коллекторлар, визуалды/мәтіндік салыстыру;
- Seismic / Geophysics: 2D/3D, lines/volumes, SEG-Y;
- Documents / Evidence және Integrations.

## 4. Ағымдағы мәртебе

### Platform
- ✅ FastAPI/PostGIS, Evidence, About RU/KK/EN, Help RU/KK/EN;
- 🧪 толық CI қайта тексеріледі.

### External data
- ✅ ExternalDataSource/Record/SyncRun/EntityLink;
- ✅ ExternalDataConnector және Kazakhstan Open Data API v4 connector;
- ⬜ persistence/manual/scheduled sync және басқа connectors.

### Spatial
- ✅ Territory Explorer / Geological Entity Passport;
- ✅ PostGIS nearby search;
- ✅ нүкте/үтір coordinate models;
- ✅ projected X/Y + CRS + axis order;
- 🧪 толық HTTP coordinate workflow;
- ⬜ PROJ/pyproj және Kazakhstan/local CRS presets.

### Subsurface
- ✅ trajectory, well logs, tests, core, seismic models;
- ✅ Well Passport API;
- 🧪 migration/integration validation;
- ⬜ LAS/DLIS/WITSML және SEG-Y import.

### Well Correlation
- ✅ WellMarker + migration 0004;
- ✅ correlation API/service;
- ✅ TVDSS-preferred marker comparison және depth-reference safety;
- ✅ marker depth delta;
- ✅ бірдей local horizons салыстыру;
- ✅ thickness және net-pay delta;
- ✅ porosity/permeability, lithology, fluid және hydrocarbon-status differences;
- 🧪 CI/PostGIS integration tests;
- ⬜ log-curve assisted correlation;
- ⬜ PySide6 cross-section viewer.

### Documentation
- ✅ RU/KK/EN user guides;
- ✅ RU/KK/EN roadmaps;
- ✅ Documentation Policy;
- ✅ CI documentation-contract test.

## 5. Жақын P0 backlog
1. Толық Ruff/pytest/CI.
2. PostgreSQL/PostGIS integration + migration-to-head test.
3. Coordinate search HTTP endpoint және PROJ/pyproj.
4. External sync persistence/manual endpoint.
5. Kazakhstan Open Data dataset registry.
6. Correlation integration tests және demo markers/intervals.
7. Unit tests marker/reservoir comparison.
8. Core Dataset manifest және controlled vocabularies.
9. Audit/revisions.
10. PySide6 correlation-viewer data model prototype.

## 6. Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation;
- `v0.3`: CRS + correlation hardening;
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y;
- `v0.5`: scheduled sync/matching/review;
- `v0.6`: unified RU/KK/EN search;
- `v0.7`: GIS/PySide6 + correlation viewer;
- `v1.0`: production GeoKZ Desktop.

## 7. Definition of Done
Функция implementation, validation, tests, migration, RU/KK/EN help, үш user guide, үш roadmap, provenance және жасыл CI болған кезде ғана аяқталды деп саналады.
