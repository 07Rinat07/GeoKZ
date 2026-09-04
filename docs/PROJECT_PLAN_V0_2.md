# GeoKZ — актуальный план развития v0.2+

Статус документа: `2026-09-04`, ветка `feature/external-data-sync-v0.2`.

Обозначения: `✅` реализовано в коде; `🧪` реализовано/частично реализовано, требует CI или интеграционной проверки; `⬜` запланировано.

## 1. Продуктовый смысл

GeoKZ — единое рабочее окно по геологической информации Казахстана. Пользователь выбирает территорию, координату, месторождение, структуру или скважину и получает максимально полную доступную информацию из встроенной проверенной базы и разрешённых внешних источников.

Основной путь:

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
6. Базовый GeoKZ Core Dataset работает без обязательного интернета.
7. Приложение, схема БД, Core Dataset и внешние источники обновляются независимо.
8. PostGIS является основой пространственных запросов.
9. Числовые измерения сохраняют units и reference system.
10. MD/TVD/TVDSS не смешиваются без явного преобразования.
11. Наблюдение и интерпретация — разные сущности.
12. По неоднозначным координатам CRS не угадывается молча.

## 3. Основные домены

### Territory / Spatial
- административные регионы;
- поиск по области/району;
- поиск по широте/долготе;
- ввод проекционных X/Y;
- CRS/axis-order normalization;
- ближайшие скважины/объекты/сейсмика;
- расстояния PostGIS geography;
- карта, DEM, гидрография, land cover и инфраструктура при наличии разрешённых данных.

### Field / Geological Object
- положение;
- тектоника;
- стратиграфия;
- литология;
- продуктивные горизонты;
- нефть/газ/вода;
- свойства коллекторов;
- pressure/temperature;
- скважины;
- сейсмика;
- история изучения;
- источники и конфликты.

### Well / Wellbore
- паспорт;
- координаты;
- траектория MD/TVD/TVDSS;
- интервалы;
- formation tops / markers;
- ГИС/well logs;
- керн/образцы;
- испытания;
- дебиты нефти/газа/воды;
- pressure/temperature;
- документы/evidence.

### Well Correlation
- опорная и соседние скважины;
- стратиграфические/геофизические реперы;
- визуальные колонки разрезов;
- линии одинаковых реперов;
- литологические интервалы;
- выделение коллекторов;
- нефть/газ/вода;
- текстовые различия глубин и мощности;
- сопоставление по TVDSS с безопасным fallback;
- provenance каждой корреляционной отметки;
- ручная экспертная корректировка на будущем этапе.

### Seismic / Geophysics
- 2D/3D surveys;
- lines/volumes;
- coverage;
- acquisition metadata;
- processing history;
- SEG-Y catalog;
- горизонты/разломы/интерпретации.

### Documents / Evidence
- Source / Document / Page;
- Fact / Evidence / Conflict;
- revisions/audit;
- OCR/raw text;
- object/file storage.

### Integrations
- RAW staging;
- checksum/diff;
- normalization;
- matching;
- review queue;
- manual/periodic sync.

## 4. Текущий статус кода

### Platform / API
- ✅ FastAPI + `/api/v1`;
- ✅ PostgreSQL/PostGIS schema foundation;
- ✅ evidence model;
- ✅ API «О программе» RU/KK/EN;
- ✅ авторские metadata Sarmuldin Rinat / ura07srr@gmail.com;
- ✅ контекстный help catalog RU/KK/EN;
- ✅ help API;
- 🧪 общий CI требует повторной проверки после последних изменений.

### External data
- ✅ ExternalDataSource / ExternalRecord / ExternalSyncRun / ExternalEntityLink;
- ✅ общий `ExternalDataConnector` Protocol;
- ✅ SHA-256 checksum;
- ✅ Kazakhstan Open Data API v4 connector;
- ✅ секреты через environment;
- ⬜ persistence sync use case;
- ⬜ manual sync endpoint;
- ⬜ registry официальных datasets;
- ⬜ scheduled sync;
- ⬜ USGS/Macrostrat/OGC connectors.

### Territory / spatial search
- ✅ Territory Explorer contract/service;
- ✅ Geological Entity Passport contract/service;
- ✅ PostGIS nearby search service;
- ✅ coordinate input models принимают точку и запятую;
- ✅ projected X/Y model с CRS и axis order;
- 🧪 HTTP endpoint для полного coordinate workflow/CRS transformation;
- ⬜ pyproj/PROJ transformation service;
- ⬜ CRS presets Казахстана и локальные CRS организации;
- ⬜ spatial integration tests.

### Subsurface
- ✅ WellTrajectoryPoint model;
- ✅ WellLogRun / WellLogCurve;
- ✅ WellTest;
- ✅ CoreRun / CoreSample;
- ✅ SeismicSurvey / SeismicLine / SeismicVolume;
- ✅ агрегированный Well Passport API;
- 🧪 migration/integration validation после последних изменений;
- ⬜ LAS/DLIS/WITSML import;
- ⬜ SEG-Y catalog/import metadata.

### Well correlation
- ✅ `WellMarker` model;
- ✅ migration `20260904_0004`;
- ✅ correlation response contract;
- ✅ comparison service с предпочтением TVDSS;
- ✅ distance from reference well;
- ✅ marker depth deltas;
- ✅ защита от несопоставимых depth references;
- ✅ API `/api/v1/correlation/wells/{reference_well_id}`;
- 🧪 CI/integration tests;
- ⬜ вычисление различий мощности коллектора;
- ⬜ корреляция по ГИС-кривым;
- ⬜ ручное соединение/разрыв корреляционных линий;
- ⬜ визуальный cross-section viewer в PySide6;
- ⬜ экспорт correlation section в PDF/PNG/GeoPackage metadata.

### Documentation
- ✅ USER_GUIDE_RU;
- ✅ USER_GUIDE_KK;
- ✅ USER_GUIDE_EN;
- ✅ Documentation Policy;
- ✅ I18N specification;
- ✅ Business Domain document;
- ✅ roadmap поддерживается в этой ветке;
- ⬜ CI contract для обязательного наличия синхронных RU/KK/EN user docs.

## 5. Ближайший P0 backlog

1. Исправить/прогнать Ruff + pytest на полном текущем head.
2. Добавить PostgreSQL/PostGIS service в CI и migration test до `head`.
3. Закрыть coordinate-search HTTP endpoint.
4. Реализовать pyproj/PROJ CRS transformation.
5. Добавить preset/catalog распространённых CRS + локальные настраиваемые CRS.
6. Persistence service для ExternalRecord/SyncRun.
7. Manual sync endpoint.
8. Registry первых официальных Kazakhstan Open Data datasets.
9. Integration tests для nearby search и correlation.
10. Добавить seed markers/intervals для демонстрации корреляции.
11. Расширить текстовую корреляцию сравнением толщины коллекторов и флюидов.
12. Добавить documentation CI contract RU/KK/EN.
13. Core Dataset manifest/importer.
14. Controlled vocabularies для lithology/marker/property kinds/units.
15. Audit log/revisions.

## 6. План релизов

### v0.2 — platform foundation
Интеграции, provenance, RU/KK/EN, help system, territory/entity/well API, coordinate models, базовая subsurface и correlation foundation.

### v0.3 — spatial + subsurface hardening
Полный coordinate workflow, CRS transformations, PostGIS integration tests, stable Well Passport, correlation engine, demo data, unit vocabularies.

### v0.4 — files and logs
PDF/DOCX, LAS/DLIS/WITSML, SEG-Y metadata, object storage, OCR, file provenance.

### v0.5 — synchronization + matching
Scheduled Kazakhstan Open Data, USGS/Macrostrat, incremental sync, matching, review queue, audit.

### v0.6 — unified search
RU/KK/EN full text, aliases, spatial/depth/fluid/lithology/log/test/seismic filters.

### v0.7 — GIS/Desktop visualization
MapLibre/PySide6, maps, cross-well correlation viewer, depth tracks, seismic coverage, GeoPackage/QGIS.

### v0.8 — geological model hardening
Controlled vocabularies, GeologicalUnit, StratigraphicUnit, Lithology, GeologicalAge, Fault/Contact, reservoir concepts, GeoSciML alignment.

### v0.9 — AI-assisted extraction
Только candidates + human review; никаких прямых verified updates.

### v1.0 — production desktop
RU/KK/EN, Territory Explorer, Coordinate Search, Field Passport, Well Passport, Correlation Viewer, updates center, documents/evidence, network mode и offline core/cache.

## 7. Definition of Done пользовательской функции

Функция считается завершённой только если:

1. есть рабочий API/domain implementation;
2. есть validation/error handling;
3. есть tests;
4. обновлена БД/migration при необходимости;
5. обновлены RU/KK/EN подсказки;
6. обновлены `USER_GUIDE_RU/KK/EN`;
7. обновлён этот roadmap;
8. данные имеют provenance/verification там, где это применимо;
9. UI не скрывает неоднозначность CRS/depth/unit;
10. CI зелёный.
