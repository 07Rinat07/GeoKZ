# GeoKZ — актуальный план развития v0.3+

Статус: `2026-09-05`, текущий feature-срез `feature/geological-study-license-review-v0.3`.

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
- visual cross-section backend view-model:
  `POST /api/v1/correlation/wells/view`;
- synthetic end-to-end demo:
  `POST /api/v1/correlation/demo/workflow`;
- официальный Kazakhstan Open Data connector с metadata/mapping/schema inspection;
- scheduler + Update All:
  `POST /api/v1/integrations/sync-all`,
  `GET /api/v1/integrations/scheduler/status`,
  `POST /api/v1/integrations/scheduler/run-due`;
- `kz-egov-oil-gas-fields` (`stat_kgn_117/v10`) RAW → normalization → deterministic field matching → review;
- field processing:
  `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process`;
- technical review queue:
  `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`;
- localized review UI/view-model:
  `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`;
- controlled vocabulary registry (`lithology`, `marker_type`, `property_kind`, `unit`) и canonical bindings к subsurface records при сохранении RAW/source wording;
- исправлен cartesian-product SQLAlchemy warning в correlation distance query и добавлен PostGIS regression test.

## Текущий P0 — реестр лицензий на геологическое изучение недр

Источник:

```text
GeoKZ code:  kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

В текущей feature-ветке реализованы:

- normalizer административных полей лицензии;
- сохранение исходного `raw_payload`;
- нормализованные `license_number`, `issue_date`, license type/scope, term, basis, authority, holder и BIN;
- Alembic `20260905_0008` с generic record-review metadata: `reviewed_by`, `reviewed_at`, `review_comment`;
- record-level `REVIEW_REQUIRED → ACCEPTED/REJECTED`;
- отсутствие автоматического `ExternalEntityLink`, потому что проверенная карточка v6 не содержит стабильного geological-object/geometry identifier;
- upstream `CHANGED` инвалидирует старое human review;
- unit + PostgreSQL/PostGIS HTTP integration tests;
- отдельные RU/KK/EN инструкции.

API:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

Merge gate текущего P0: final exact-head `compileall + Ruff + pytest` и PostgreSQL/PostGIS integration должны быть зелёными; затем PR-CI на том же head и squash-merge в `main`.

## Следующий P0 после merge

### 1. GeoKZ Core Dataset manifest/importer

Нужен versioned baseline, который устанавливается вместе с приложением и обновляется независимо от `.exe`:

- `manifest.json`: dataset version, schema version, created_at, SHA-256;
- transactional import/upgrade + rollback;
- bootstrap entities/sources/facts/regions/vocabularies;
- отдельная версия Core Dataset в About/Data Sources;
- checksum validation и подготовка digital signature;
- тесты повторного импорта, несовместимой schema version и rollback.

### 2. Authentication + AuditLog/Revision

После baseline:

- users/roles: expert/editor/admin;
- audit trail для review и изменения scientific master data;
- revision history для Fact/Entity/geometry/interpretation;
- verified данные нельзя silently overwrite;
- подготовить административный write API для controlled vocabularies только после audit/roles.

### 3. Production PySide6 review/data-source screens

- «Источники данных» + «Обновить всё»;
- due/running/error/status/version;
- field review queue по server-owned action descriptors;
- license record review ACCEPT/REJECT;
- provenance panel;
- contextual help RU/KK/EN.

### 4. Расширение официальных Kazakhstan connectors

Подключать следующие геологические/недропользовательские datasets через общий provider SDK только после проверки current metadata/mapping/license/terms. Каждый source должен иметь RAW, checksum/diff, typed normalizer, review rules и contract tests; не копировать бизнес-логику отдельным route/service для каждого dataset без необходимости.

### 5. Global/open geology context

После стабилизации официальных Kazakhstan sources:

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
