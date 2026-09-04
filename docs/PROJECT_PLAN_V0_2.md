# GeoKZ — план развития v0.2+

## 1. Продуктовое назначение

GeoKZ — единое рабочее окно по геологической информации Казахстана.

Пользователь должен иметь возможность выбрать территорию, месторождение, структуру или скважину и получить максимально полную доступную информацию из собственной проверенной базы и подключённых разрешённых источников.

Главный пользовательский путь:

```text
Территория
  ↓
Месторождения / структуры / скважины / сейсмика / карты
  ↓
Месторождение
  ↓
Геология → стратиграфия → литология → залежи → скважины
  ↓
Скважина
  ↓
Траектория → интервалы → ГИС → керн → испытания → нефть/газ/вода
  ↓
Источник / документ / файл / страница / доказательство
```

Подробная предметная модель: `docs/BUSINESS_DOMAIN.md`.

## 2. Обязательные принципы

1. **Три языка:** русский (`ru`), казахский (`kk`) и английский (`en`) во всём пользовательском продукте.
2. **Полнота с provenance:** значение без понятного происхождения не считается проверенным мастер-данным.
3. **Исходный материал неизменяем:** цитата, OCR/raw text, LAS/DLIS/SEG-Y и RAW API payload сохраняются отдельно от интерпретации.
4. **Human-in-the-loop:** внешние API и ИИ не переписывают проверенные факты автоматически.
5. **Offline-capable core:** встроенная база должна быть полезна без интернета.
6. **Обновляемые наборы:** приложение, GeoKZ Core Dataset и внешние источники имеют независимые версии.
7. **GIS-first:** PostGIS/GeoJSON, далее GeoPackage, OGC API Features и QGIS.
8. **Отраслевые форматы:** архитектура не должна препятствовать LAS/DLIS, WITSML, SEG-Y, GeoSciML, RESQML/PRODML.
9. **Измерения с единицами:** числовые геологические/геофизические параметры всегда имеют unit и, при необходимости, reference system.
10. **Наблюдение отдельно от интерпретации:** измеренный приток газа и вывод «продуктивный горизонт» — разные сущности.

## 3. Целевая архитектура

```text
PySide6 / Web / QGIS / CLI
            │
            ▼
        FastAPI /api/v1
            │
            ▼
      Application Layer
 ┌──────────┼──────────────────────────────────┐
 │          │          │          │             │
Catalog  Evidence   Subsurface   Search    Integrations
 │          │          │          │             │
 └──────────┴──────────┴──────────┴─────────────┘
            │
            ▼
        Domain Model
            │
            ▼
 Infrastructure / Repositories
     │              │                 │
PostgreSQL       Object/File       External
 + PostGIS         Storage         Connectors
```

Большие файлы не помещаются целиком в обычные ORM-таблицы:

- PDF/DOCX;
- LAS/DLIS;
- SEG-Y;
- растры;
- большие массивы кривых.

PostgreSQL хранит каталог, metadata, geometry, индексы, связи, контроль качества и provenance; файл хранится в file/object storage.

## 4. Главные домены

### Territory / Spatial

- административные регионы;
- карта;
- геологические/тектонические объекты;
- рельеф/DEM;
- гидрография;
- инфраструктура и land-cover при наличии открытых источников.

### Field / Deposit

- положение;
- геологическое строение;
- тектоника;
- стратиграфия;
- продуктивные горизонты;
- литология;
- нефть/газ/вода;
- свойства коллекторов;
- давления/температуры;
- скважины;
- сейсмика;
- история изучения;
- источники и конфликты.

### Well / Wellbore

- паспорт;
- координаты;
- траектория MD/TVD/TVDSS;
- геологический разрез;
- formation tops;
- интервалы;
- ГИС/well logs;
- керн/образцы;
- испытания;
- притоки нефти/газа/воды;
- pressure/temperature;
- документы и evidence.

### Seismic / Geophysics

- 2D surveys/lines;
- 3D surveys/volumes;
- acquisition metadata;
- processing history;
- SEG-Y dataset catalog;
- interpretations: horizons/faults/contacts;
- spatial coverage.

### Documents / Evidence

- Source;
- Document;
- Page;
- Fact;
- Evidence;
- Conflict;
- revisions/audit.

### Integrations

- RAW external records;
- normalization;
- checksum/diff;
- entity matching;
- review queue;
- periodic/manual sync.

## 5. Модель данных по происхождению

```text
RAW         — неизменённая запись/файл внешнего источника
NORMALIZED  — приведённое к модели GeoKZ представление
VERIFIED    — проверенные мастер-данные GeoKZ
```

Внешняя синхронизация никогда не выполняет прямой overwrite проверенных геологических значений.

## 6. GeoKZ Core Dataset

Приложение поставляется с базовым набором:

- административные регионы Казахстана;
- основные бассейны и структуры;
- базовые месторождения/объекты;
- пилотные скважины и интервалы;
- базовая стратиграфия/литология;
- проверенные источники и факты;
- `ru/kk/en` названия там, где они известны.

Версии независимы:

```text
GeoKZ App:          0.2.0
Database schema:    3+
GeoKZ Core Dataset: 2026.09
```

## 7. Внешние источники

Приоритет:

1. Kazakhstan Open Data (`data.egov.kz`);
2. другие официальные открытые казахстанские наборы/GIS-сервисы с понятной лицензией;
3. USGS;
4. Macrostrat;
5. OneGeology / OGC;
6. Copernicus;
7. корпоративные WITSML/OSDU endpoints — только как отдельные настраиваемые интеграции, если организация предоставляет доступ.

Для каждого dataset сохраняются условия использования, dataset/version, время получения и raw payload/checksum.

## 8. Синхронизация

Режимы:

- вручную: «Обновить источник» / «Обновить всё»;
- автоматически: периодическая фоновая проверка.

Pipeline:

```text
External API / Dataset
       ↓
Connector
       ↓
RAW staging
       ↓
checksum / dedup / diff
       ↓
normalization
       ↓
entity/well/field matching
       ↓
SAFE metadata OR REVIEW_REQUIRED
       ↓
review
       ↓
verified master view
```

Неуспешное обновление не должно блокировать работу приложения.

## 9. Трёхъязычность

Подробности: `docs/I18N.md`.

Поддерживаются `ru`, `kk`, `en` для UI, названий, справочников, поиска, документации и пользовательских сообщений. Исходный текст источника не заменяется переводом.

## 10. Отраслевые ориентиры

GeoKZ не обязан реализовывать стандарты полностью, но проектируется совместимо с ними:

- **WITSML 2.1** — well/drilling/trajectory/well-log data;
- **Energistics PWLS** — классификация well-log property kinds;
- **SEG-Y rev 2.x** — seismic exchange;
- **GeoSciML** — геологические объекты;
- **OGC API Features / GeoPackage** — GIS interoperability;
- **OSDU DDMS concepts** — ориентир для разделения wellbore/seismic domain services на будущих этапах.

## 11. План релизов

### v0.2 — фундамент платформы

- [x] FastAPI/PostgreSQL/PostGIS skeleton;
- [x] evidence model;
- [x] `/api/v1`;
- [x] ExternalDataSource / ExternalRecord / ExternalSyncRun / ExternalEntityLink;
- [x] Connector Protocol;
- [x] read API статуса источников;
- [x] `ru/kk/en` contract и API «О программе»;
- [x] авторские metadata проекта;
- [x] первый Kazakhstan Open Data API v4 connector;
- [x] checksum внешних RAW-записей;
- [ ] persistence sync use case;
- [ ] ручной sync endpoint;
- [ ] integration tests PostgreSQL/PostGIS;
- [ ] registry официальных datasets;
- [ ] Core Dataset manifest/importer.

### v0.3 — subsurface foundation

- траектория скважины;
- well-log run/curve metadata;
- испытания скважин/пластов;
- керн/образцы;
- seismic survey/line/volume catalog;
- унифицированные depth references;
- унифицированные units/property kinds;
- API полного паспорта скважины.

### v0.4 — документы и файлы

- PDF/DOCX import;
- LAS/DLIS catalog/import;
- SEG-Y catalog/import metadata;
- SHA-256/object storage;
- постраничное извлечение текста;
- OCR fallback;
- language detection;
- связь файлов с объектом/скважиной/исследованием.

### v0.5 — synchronization + matching

- Kazakhstan Open Data scheduled sync;
- USGS connector;
- Macrostrat connector;
- incremental sync;
- entity/well matching;
- deduplication;
- review queue;
- audit/revisions.

### v0.6 — unified search

- `pg_trgm`;
- full-text `ru/kk/en`;
- aliases/transliteration;
- spatial PostGIS search;
- поиск по глубине/интервалам/флюиду/литологии;
- поиск по ГИС/испытаниям/сейсмическому покрытию.

### v0.7 — GIS application

- MapLibre;
- GeoJSON API;
- bbox/intersects/within/distance;
- слои месторождений/скважин/сейсмики/геологии;
- GeoPackage export;
- QGIS integration.

### v0.8 — geological model

- controlled vocabularies;
- GeologicalUnit / StratigraphicUnit / Lithology / GeologicalAge;
- Fault / Contact;
- Basin / Field / Deposit / Occurrence;
- reservoir intervals;
- harmonization с GeoSciML/Energistics concepts.

### v0.9 — AI-assisted extraction

ИИ создаёт только candidates:

- EntityCandidate;
- WellCandidate;
- IntervalCandidate;
- FactCandidate;
- EvidenceCandidate;
- RelationCandidate.

Публикация — только после validation/review.

### v1.0 — GeoKZ Desktop

- PySide6;
- RU/KK/EN;
- Territory Explorer;
- Field/Deposit Passport;
- Well Passport;
- depth track viewer;
- well-log viewer metadata/curves;
- seismic catalog/map coverage;
- documents/evidence;
- source comparison;
- data update center;
- network mode;
- offline core/cache.

## 12. P0 backlog

1. Завершить CI текущего v0.2 среза.
2. Persistence service для ExternalRecord и SyncRun.
3. Manual sync use case/API.
4. Registry первых Kazakhstan Open Data datasets.
5. PostgreSQL/PostGIS integration tests.
6. Core Dataset manifest.
7. WellTrajectoryPoint model.
8. WellLogRun / WellLogCurve metadata models.
9. WellTest model.
10. SeismicSurvey / SeismicLine / SeismicVolume models.
11. CoreRun / CoreSample models.
12. API агрегированного Well Passport.
13. API Territory Explorer.
14. API Field Passport.
15. Controlled vocabularies + unit model.
16. Audit log/revisions.
17. RU/KK/EN search.
18. Spatial indexes/queries.
19. Document/file storage abstraction.
20. Review queue.

## 13. Definition of Done внешнего connector

1. задокументированы API/лицензия/версия набора;
2. секреты только через environment/config;
3. RAW сохраняется без потери данных;
4. импорт идемпотентен;
5. stable external id + checksum;
6. транзакционная обработка ошибок;
7. unit/integration tests;
8. языковые варианты не смешиваются;
9. статус доступен приложению;
10. verified master data не изменяются автоматически.

## 14. Definition of Done subsurface observation

1. привязка к объекту/скважине;
2. depth/reference system определены;
3. числовое значение имеет unit;
4. оригинальная единица не теряется;
5. есть source/evidence либо явно указан статус неизвестного происхождения;
6. observation отделён от interpretation;
7. поддерживается verification status;
8. импорт повторяем и идемпотентен;
9. API не зависит от конкретного файлового формата;
10. данные доступны на `ru/kk/en` там, где локализация применима.
