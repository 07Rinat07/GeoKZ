# GeoKZ — актуальный план развития v0.2+

Статус документа: `2026-09-04`, ветка `feature/external-data-sync-v0.2`.

Обозначения: `✅` реализовано в коде; `🧪` реализовано/частично реализовано, требует CI или интеграционной проверки; `⬜` запланировано.

## 1. Продуктовый смысл
GeoKZ — единое рабочее окно по геологической информации Казахстана. Пользователь выбирает территорию, координату, месторождение, структуру или скважину и получает максимально полную доступную информацию из встроенной проверенной базы и разрешённых внешних источников.

```text
Территория / координата
  ↓
месторождения / структуры / скважины / сейсмика / карты
  ↓
паспорт геологического объекта
  ↓
паспорт скважины
  ↓
траектория / интервалы / литология / ГИС / керн / испытания / нефть-газ-вода
  ↓
корреляция с соседними скважинами
  ↓
источник / документ / файл / страница / доказательство
```

## 2. Обязательные правила
1. RU/KK/EN во всём пользовательском продукте.
2. Документация и инструкции входят в Definition of Done.
3. Значимые данные имеют provenance и verification status.
4. Исходные документы, RAW API payload, LAS/DLIS/SEG-Y не заменяются интерпретацией.
5. Внешние API и ИИ не переписывают verified master data автоматически.
6. GeoKZ Core Dataset работает без обязательного интернета.
7. Приложение, схема БД, Core Dataset и внешние источники обновляются независимо.
8. PostGIS — основа пространственных запросов.
9. Измерения сохраняют units/reference system.
10. MD/TVD/TVDSS не смешиваются без явного преобразования.
11. Наблюдение и интерпретация — разные сущности.
12. Неоднозначный CRS не угадывается молча.

## 3. Домены

### Territory / Spatial
Области/районы, карта, latitude/longitude, projected X/Y, CRS/axis order, ближайшие скважины/объекты/сейсмика, PostGIS geography distance, DEM/гидрография/land cover при наличии разрешённых данных.

### Field / Geological Object
Положение, тектоника, стратиграфия, литология, продуктивные горизонты, коллекторы, нефть/газ/вода, pressure/temperature, скважины, сейсмика, история изучения, источники и конфликты.

### Well / Wellbore
Паспорт, координаты, trajectory MD/TVD/TVDSS, intervals, formation tops/markers, well logs, керн, tests, дебиты, pressure/temperature, documents/evidence.

### Well Correlation
Опорная/соседние скважины, реперы, визуальные колонки, линии общих реперов, литология, коллекторы, нефть/газ/вода, различия глубин/мощности/net pay/пористости/проницаемости/флюида, TVDSS-preferred alignment и provenance.

### Seismic / Geophysics
2D/3D, lines/volumes, coverage, acquisition/processing metadata, SEG-Y catalog и interpretations.

### Documents / Evidence
Source/Document/Page, Fact/Evidence/Conflict, revisions/audit, OCR/raw text, file/object storage.

### Integrations
RAW staging, checksum/diff, normalization, matching, review queue, manual/periodic sync.

## 4. Текущий статус кода

### Platform / API
- ✅ FastAPI + `/api/v1`;
- ✅ PostgreSQL/PostGIS foundation;
- ✅ evidence model;
- ✅ About API RU/KK/EN;
- ✅ авторские metadata Sarmuldin Rinat / ura07srr@gmail.com;
- ✅ contextual Help catalog/API RU/KK/EN;
- 🧪 полный CI требует повторной проверки после последних изменений.

### External data
- ✅ ExternalDataSource / ExternalRecord / ExternalSyncRun / ExternalEntityLink;
- ✅ `ExternalDataConnector` Protocol;
- ✅ SHA-256 checksum;
- ✅ Kazakhstan Open Data API v4 connector;
- ✅ secrets через environment;
- ⬜ persistence/manual/scheduled sync;
- ⬜ official dataset registry;
- ⬜ USGS/Macrostrat/OGC connectors.

### Territory / spatial
- ✅ Territory Explorer;
- ✅ Geological Entity Passport;
- ✅ PostGIS nearby-search service;
- ✅ coordinate models: точка/запятая;
- ✅ projected X/Y + CRS + axis order;
- 🧪 полный HTTP coordinate workflow;
- ⬜ PROJ/pyproj transformation;
- ⬜ Kazakhstan/local CRS presets;
- ⬜ spatial integration tests.

### Subsurface
- ✅ WellTrajectoryPoint;
- ✅ WellLogRun / WellLogCurve;
- ✅ WellTest;
- ✅ CoreRun / CoreSample;
- ✅ SeismicSurvey / SeismicLine / SeismicVolume;
- ✅ Well Passport API;
- 🧪 migration/integration validation;
- ⬜ LAS/DLIS/WITSML import;
- ⬜ SEG-Y catalog/import metadata.

### Well correlation
- ✅ `WellMarker` model;
- ✅ migration `20260904_0004`;
- ✅ correlation response/service/API;
- ✅ distance from reference well;
- ✅ TVDSS-preferred marker comparison;
- ✅ marker depth deltas;
- ✅ защита от несовместимых depth references;
- ✅ сравнение одинаковых local horizons;
- ✅ thickness delta;
- ✅ net-pay delta;
- ✅ porosity/permeability comparison;
- ✅ lithology/fluid/hydrocarbon-status differences;
- 🧪 CI/PostGIS integration tests;
- ⬜ correlation по ГИС-кривым;
- ⬜ ручное соединение/разрыв линий;
- ⬜ PySide6 cross-section viewer;
- ⬜ export PDF/PNG.

### Documentation
- ✅ USER_GUIDE RU/KK/EN;
- ✅ roadmap RU/KK/EN;
- ✅ Documentation Policy;
- ✅ I18N/Business Domain docs;
- ✅ CI test обязательного наличия трёх guides и трёх roadmaps.

## 5. Ближайший P0 backlog
1. Полный Ruff + pytest на текущем head.
2. PostgreSQL/PostGIS service в CI + migrate-to-head test.
3. Coordinate-search HTTP endpoint.
4. PROJ/pyproj CRS transformation.
5. CRS presets Казахстана + локальные настраиваемые CRS.
6. Persistence service ExternalRecord/SyncRun.
7. Manual sync endpoint.
8. Registry первых Kazakhstan Open Data datasets.
9. Integration tests nearby search + correlation.
10. Seed markers/intervals для демонстрации корреляции.
11. Unit tests marker/reservoir comparison.
12. Core Dataset manifest/importer.
13. Controlled vocabularies lithology/marker/property kinds/units.
14. Audit log/revisions.
15. Prototype visual correlation data model for PySide6.

## 6. План релизов
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation;
- `v0.3`: CRS, spatial/subsurface hardening, correlation engine + demo data;
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y files;
- `v0.5`: scheduled sync, matching, review/audit;
- `v0.6`: unified RU/KK/EN search;
- `v0.7`: GIS/PySide6 + visual correlation viewer;
- `v0.8`: geological model hardening;
- `v0.9`: AI candidates + human review;
- `v1.0`: production GeoKZ Desktop.

## 7. Definition of Done пользовательской функции
Функция завершена только если есть implementation, validation, tests, migration при необходимости, RU/KK/EN help, три user guides, три roadmaps, provenance/verification правила и зелёный CI.
