# GeoKZ — актуальный план развития v0.3+

Статус: `2026-09-05`, текущий feature-срез `feature/core-dataset-manifest-importer-v0.3`.

## Цель

GeoKZ должен быть единым evidence-based геологическим рабочим окном Казахстана: территория/координата → ближайшие месторождения, структуры, скважины и сейсмика → паспорта → глубинные интервалы, литология, коллекторы, ГИС, керн и испытания → корреляция соседних скважин → первичные источники, provenance, конфликты и экспертная проверка.

Приложение и пользовательская документация поддерживаются на RU/KK/EN. Внешние API обогащают локальную базу, но не являются обязательной runtime-зависимостью и не переписывают verified master data автоматически.

## Реализовано и слито в main

- FastAPI + PostgreSQL 17/PostGIS 3.5 + async SQLAlchemy + Alembic;
- real PostgreSQL/PostGIS CI с миграциями до head;
- territory explorer, Geological Entity Passport и Well Passport;
- географический и projected X/Y ввод, точка/запятая, WGS84/UTM helper;
- persistent organization-local CRS registry с EPSG/WKT/PROJ и confirmation;
- PostGIS nearby search;
- WellTrajectoryPoint, WellLogRun/Curve, WellTest, CoreRun/CoreSample, SeismicSurvey/Line/Volume;
- WellMarker и безопасная корреляция TVDSS/TVD/MD;
- visual cross-section backend view-model: `POST /api/v1/correlation/wells/view`;
- synthetic end-to-end demo: `POST /api/v1/correlation/demo/workflow`;
- официальный Kazakhstan Open Data connector с metadata/mapping/schema inspection;
- scheduler + Update All;
- `kz-egov-oil-gas-fields` (`stat_kgn_117/v10`) RAW → normalization → deterministic field matching → review;
- localized field-review UI/view-model;
- controlled vocabulary registry (`lithology`, `marker_type`, `property_kind`, `unit`) и canonical bindings;
- исправлен cartesian-product warning в correlation distance query;
- `kz-egov-geological-study-licenses` (`zher_koinauyn_geologiyalyk_zer2/v6`) RAW → typed administrative normalization → record-level `REVIEW_REQUIRED → ACCEPTED/REJECTED` без недоказуемого entity matching;
- Alembic `20260905_0008` с generic external-record reviewer metadata;
- license review unit + PostgreSQL/PostGIS HTTP integration tests и RU/KK/EN documentation.

Последний merged baseline main: PR #11, merge SHA `f70675699aaae53b89eca23f29fefc61bdf78101`.

## Текущий P0 — GeoKZ Core Dataset manifest/importer

Цель: versioned baseline, который поставляется вместе с приложением и обновляется независимо от Alembic schema migrations и provider sync versions.

В текущей feature-ветке реализованы:

- Alembic `20260905_0009` и `CoreDatasetState` для installed dataset state;
- manifest schema v1 с `dataset_code`, `dataset_version`, `schema_version`, `created_at`, namespace, dependencies и per-file SHA-256;
- защита от absolute/path traversal;
- required-file и checksum validation до DB write;
- typed parser для sources, regions, entities и facts;
- duplicate `external_id` validation;
- `geokz-core:` namespace policy;
- bundle-internal reference validation;
- transactional upsert + rollback;
- idempotence по manifest SHA-256 (`changed=false` при повторном импорте);
- bundled snapshot `2026.09.0-bootstrap`;
- intentionally minimal bootstrap: internal metadata source + country-level Kazakhstan navigation record без утверждения boundary geometry, без вымышленных geological entities/facts;
- REST status/install API;
- CLI validate/install/status;
- bundled Core Dataset version в About;
- unit tests checksum/path traversal/schema/duplicate/reference;
- PostgreSQL/PostGIS integration на install/idempotence и rollback;
- отдельная документация `CORE_DATASET_RU/KK/EN.md`.

API:

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=ru
POST /api/v1/core-dataset/install?lang=ru
```

CLI:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Schema v1 использует `schema_version` как фактический compatibility gate. `minimum_app_version` пока informational metadata; строгая SemVer-policy не имитируется самодельным сравнением версий.

Merge gate текущего P0: README + USER_GUIDE + roadmap + documentation policy RU/KK/EN, final exact-head `compileall + Ruff + pytest`, PostgreSQL/PostGIS integration, затем PR-CI на том же exact head и squash-merge в `main`.

## Следующий P0 после merge

### 1. Authentication + AuditLog/Revision

- users/roles: expert/editor/admin;
- audit trail для review и изменения scientific master data;
- revision history для Fact/Entity/geometry/interpretation;
- verified данные нельзя silently overwrite;
- административные write API только через авторизацию и аудит.

### 2. Production PySide6 review/data-source screens

- «Источники данных» + «Обновить всё»;
- отдельное отображение Application / DB schema / Core Dataset / provider versions;
- Core Dataset installed/update state;
- due/running/error/status/version;
- field review queue по server-owned action descriptors;
- license record review ACCEPT/REJECT;
- provenance panel;
- contextual help RU/KK/EN.

### 3. Core Dataset update channel

После безопасного локального manifest/importer:

- signed bundle manifest;
- download/update channel;
- staging до активации;
- rollback на предыдущую установленную snapshot version;
- policy совместимости app/schema/dataset;
- audit каждой установки/rollback.

### 4. Расширение официальных Kazakhstan connectors

Подключать следующие datasets через общий provider SDK только после проверки current metadata/mapping/license/terms. Каждый source должен иметь RAW, checksum/diff, typed normalizer, review rules и contract tests.

### 5. Global/open geology context

- USGS Mineral Resources;
- Macrostrat;
- OneGeology/OGC;
- Copernicus observation assets.

Все внешние данные сохраняют source/version/retrieved_at/license/attribution. Authority не означает truth: конфликтующие значения хранятся параллельно и разрешаются экспертно.

## Definition of Done для каждого следующего среза

```text
feature branch
→ code + migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated feature docs RU/KK/EN при необходимости
→ exact-head CI green
→ PR
→ PR-CI green на том же head
→ squash merge в main
→ следующая задача
```

Главное правило остаётся неизменным: GeoKZ работает без внешних сервисов, а интернет безопасно обогащает локальную evidence-based базу.
