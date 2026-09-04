# GeoKZ — v0.2+ өзекті даму жоспары

Құжат мәртебесі: `2026-09-04`, тармақ `feature/external-data-sync-v0.2`.

Белгілер: `✅` кодта іске асырылған; `🧪` іске асырылған/ішінара іске асырылған, CI немесе интеграциялық тексеру қажет; `⬜` жоспарланған.

## 1. Өнімнің мақсаты
GeoKZ — Қазақстанның геологиялық ақпараты бойынша бірыңғай жұмыс терезесі. Пайдаланушы аумақты, координатаны, кен орнын, құрылымды немесе ұңғыманы таңдап, GeoKZ Core базасы мен рұқсат етілген сыртқы дереккөздерден барынша толық ақпарат алады.

Негізгі жол:

```text
Аумақ / координата
  ↓
кен орындары / құрылымдар / ұңғымалар / сейсмика / карталар
  ↓
геологиялық объект паспорты
  ↓
ұңғыма паспорты
  ↓
траектория / интервалдар / литология / ҰГЗ / керн / сынақтар / мұнай-газ-су
  ↓
көршілес ұңғымалар қималарын корреляциялау
  ↓
дереккөз / құжат / файл / бет / дәлел
```

## 2. Міндетті қағидалар
- RU/KK/EN барлық пайдаланушы функцияларында;
- құжаттама Definition of Done бөлігі;
- маңызды деректерде provenance және verification status бар;
- RAW/бастапқы материал интерпретациямен алмастырылмайды;
- сыртқы API және AI verified master data-ны автоматты түрде өзгертпейді;
- Core Dataset интернетсіз жұмыс істейді;
- координаттар CRS-і және MD/TVD/TVDSS анық көрсетіледі;
- өлшемдер units/reference system сақтайды.

## 3. Негізгі домендер
- Territory / Spatial: аймақ, координаталар, X/Y, CRS, жақын объектілер;
- Field / Geological Object: геология, тектоника, стратиграфия, литология, коллекторлар, мұнай/газ/су;
- Well / Wellbore: паспорт, траектория, интервалдар, ҰГЗ, керн, сынақтар;
- Well Correlation: реперлер, коллекторлар, қималарды визуалды және мәтіндік салыстыру;
- Seismic / Geophysics: 2D/3D, lines/volumes, SEG-Y каталогы;
- Documents / Evidence: source/document/page/fact/evidence/conflict;
- Integrations: RAW staging, checksum/diff, matching, review, sync.

## 4. Ағымдағы мәртебе

### Platform
- ✅ FastAPI/PostGIS foundation;
- ✅ Evidence model;
- ✅ About API RU/KK/EN;
- ✅ контекстік Help API RU/KK/EN;
- 🧪 соңғы өзгерістерден кейін толық CI қайта тексерілуі тиіс.

### External data
- ✅ ExternalDataSource/Record/SyncRun/EntityLink;
- ✅ ExternalDataConnector;
- ✅ Kazakhstan Open Data API v4 connector;
- ⬜ persistence/manual/scheduled sync;
- ⬜ official dataset registry;
- ⬜ USGS/Macrostrat/OGC connectors.

### Spatial
- ✅ Territory Explorer және Geological Entity Passport;
- ✅ PostGIS nearby search service;
- ✅ нүкте/үтір қабылдайтын coordinate models;
- ✅ projected X/Y + CRS + axis order;
- 🧪 coordinate HTTP workflow;
- ⬜ PROJ/pyproj transformation және Kazakhstan/local CRS presets.

### Subsurface
- ✅ trajectory, well logs, tests, core, seismic models;
- ✅ Well Passport API;
- 🧪 migration/integration validation;
- ⬜ LAS/DLIS/WITSML және SEG-Y import.

### Well Correlation
- ✅ WellMarker model және migration 0004;
- ✅ correlation API contract/service;
- ✅ TVDSS-preferred comparison;
- ✅ marker depth delta және incompatible depth-reference protection;
- ✅ `/api/v1/correlation/wells/{reference_well_id}`;
- ⬜ reservoir thickness comparison;
- ⬜ log-curve assisted correlation;
- ⬜ PySide6 cross-section viewer.

### Documentation
- ✅ RU/KK/EN user guides;
- ✅ Documentation Policy;
- ✅ I18N және Business Domain docs;
- ✅ RU master roadmap + KK/EN roadmap translations;
- ⬜ CI documentation contract.

## 5. Жақын P0 backlog
1. Толық Ruff/pytest/CI.
2. PostgreSQL/PostGIS integration tests және migration-to-head test.
3. Coordinate search HTTP endpoint.
4. PROJ/pyproj CRS transformation.
5. External sync persistence/manual endpoint.
6. Kazakhstan Open Data dataset registry.
7. Correlation integration tests және demo markers.
8. Коллектор қалыңдығы/флюид айырмаларын салыстыру.
9. RU/KK/EN documentation CI contract.
10. Core Dataset manifest және controlled vocabularies.

## 6. Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation;
- `v0.3`: CRS, spatial/subsurface hardening, correlation engine;
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y files;
- `v0.5`: scheduled sync, matching, review/audit;
- `v0.6`: unified RU/KK/EN search;
- `v0.7`: GIS/PySide6 visualization және correlation viewer;
- `v0.8`: geological model hardening;
- `v0.9`: AI candidates + human review;
- `v1.0`: production GeoKZ Desktop.

## 7. Пайдаланушы функциясының Definition of Done
Функция тек API/domain implementation, validation, tests, migration, RU/KK/EN help, үш user guide, үш roadmap, provenance ережелері және жасыл CI болған кезде аяқталды деп саналады.
