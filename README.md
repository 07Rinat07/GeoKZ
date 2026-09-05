# GeoKZ v0.3-dev

GeoKZ — доказательная геологическая информационная система Казахстана и единое рабочее окно для информации по территории, месторождению, структуре и скважине.

## Основные возможности

- RU / KK / EN во всём пользовательском продукте;
- территория → объект → скважина → интервал → источник;
- поиск по области/району и координатам;
- geographic latitude/longitude и projected X/Y, точка и запятая;
- WGS84/UTM helper и persistent organization-local CRS registry EPSG/WKT/PROJ;
- PostGIS-поиск ближайших скважин, объектов и сейсмики;
- паспорт геологического объекта и полный Well Passport;
- MD/TVD/TVDSS trajectory;
- литология, стратиграфия, коллекторы, нефть/газ/вода;
- ГИС/well logs, испытания, керн, 2D/3D seismic catalog;
- корреляция разрезов по реперам и интервалам;
- backend-owned visual cross-section view-model;
- synthetic end-to-end demo workflow;
- evidence/provenance, conflict storage и human review;
- versioned controlled vocabularies при сохранении RAW/source wording;
- встроенный GeoKZ Core Dataset + обновляемые внешние источники;
- контекстные подсказки и помощники RU/KK/EN.

## Ключевые правила

- **Evidence-first:** факт и интерпретация прослеживаются до источника.
- **Human-in-the-loop:** внешние API и ИИ не переписывают verified master data автоматически.
- **Offline-capable core:** базовая информация работает без обязательного интернета.
- **Independent data lifecycle:** версия GeoKZ Core Dataset отделена от версии приложения и Alembic schema revision.
- **Data provenance:** сохраняются source, upstream version, retrieved_at, checksum и RAW payload.
- **Safe depth/CRS:** MD/TVD/TVDSS и разные CRS не смешиваются молча.
- **Server-owned UI contracts:** клиент не дублирует review/correlation business rules.
- **Synthetic isolation:** demo wells не смешиваются с production wells.
- **Dedicated scheduler:** external sync выполняется отдельным process/service, не в каждом FastAPI worker.
- **Documentation-as-code:** README, user guides и roadmap поддерживаются на RU/KK/EN и проверяются CI.

## Стек

- Python 3.12;
- FastAPI;
- PostgreSQL 17 + PostGIS 3.5;
- SQLAlchemy 2 async;
- Alembic;
- Pydantic;
- Docker Compose;
- GitHub Actions CI;
- PySide6 — запланированный Windows-клиент.

## Запуск разработки

```powershell
Copy-Item .env.example .env
./scripts/dev.ps1
```

или:

```powershell
docker compose up --build
```

Swagger: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

## GeoKZ Core Dataset

GeoKZ Core Dataset — versioned baseline, который поставляется вместе с приложением, но устанавливается и обновляется отдельно от Alembic schema migrations.

Текущий bundled snapshot:

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
namespace:       geokz-core:
```

Bundle находится в `data/bootstrap/core_dataset/`. `manifest.json` хранит независимую версию набора, SHA-256 файлов, schema version, namespace и зависимости. Перед записью в БД проверяются manifest schema, path traversal, required files, checksums, payload types, duplicate `external_id` и внутренние references.

Установка выполняется одной транзакцией. Ошибка вызывает rollback; `CoreDatasetState` фиксируется только после полного успеха. Повторная установка того же manifest SHA-256 идемпотентна и возвращает `changed=false`.

Первый bootstrap намеренно не содержит вымышленных production geological facts: он включает внутреннюю metadata-запись и country-level navigation record «Республика Казахстан» без утверждения boundary geometry; `entities.jsonl` и `facts.jsonl` пока пусты.

API:

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=ru
POST /api/v1/core-dataset/install?lang=ru
```

HTTP install работает только с доверенным bundled manifest и не принимает arbitrary filesystem path.

CLI:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

`GET /api/v1/about` отдельно показывает bundled `core_dataset_version` и `core_dataset_schema_version`; фактическое installed state берётся из `/api/v1/core-dataset/status`.

Документация:
- RU: [`docs/CORE_DATASET_RU.md`](docs/CORE_DATASET_RU.md)
- KK: [`docs/CORE_DATASET_KK.md`](docs/CORE_DATASET_KK.md)
- EN: [`docs/CORE_DATASET_EN.md`](docs/CORE_DATASET_EN.md)

## Внешние источники

Приоритет: Kazakhstan Open Data → другие официальные KZ datasets/GIS → USGS → Macrostrat → OneGeology/OGC → Copernicus → корпоративные WITSML/OSDU при разрешённом доступе.

Общий принцип:

```text
external API
  → RAW
  → checksum / diff
  → normalization
  → matching или record-level review
  → human review
  → verified master view
```

### Kazakhstan Open Data

Сейчас зарегистрированы:

```text
GeoKZ code:  kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

и:

```text
GeoKZ code:  kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

GeoKZ сохраняет официальный `apiUri` без перевода/сокращения и хранит `version` отдельно. Технические names upstream fields остаются в RAW.

Официальные формы API:

```text
GET /meta/{apiUri}/{version}
GET /api/v4/mapping/{apiUri}/{version}
GET /api/v4/{apiUri}/{version}?source={JSON}
GET /api/detailed/{apiUri}/{version}?source={JSON}
```

Перед подключением/изменением dataset сначала проверяются metadata и mapping:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Каталог и регистрация:

```text
GET  /api/v1/integrations/kazakhstan/catalog
POST /api/v1/integrations/kazakhstan/register
```

Ручной sync:

```text
POST /api/v1/integrations/kazakhstan/{code}/sync
```

### API-ключ data.egov.kz

Фактический API v4 download требует developer API key.

1. Откройте `https://data.egov.kz/`.
2. Авторизуйтесь через eGov.
3. Перейдите **Разработчикам → Кабинет разработчика**.
4. Создайте/скопируйте API key.
5. Создайте локальный `.env` из `.env.example`.
6. Сохраните ключ только локально:

```env
GEOKZ_EGOV_API_KEY=ВАШ_РЕАЛЬНЫЙ_КЛЮЧ
```

7. Перезапустите backend/Docker Compose.
8. Проверьте `GET /api/v1/integrations/kazakhstan/catalog`: `api_key_configured=true`.

Реальный secret нельзя коммитить в Git, добавлять в README/код/issue/PR, публиковать на скриншотах или отправлять в чат.

Инструкции:
- RU: [`docs/EXTERNAL_API_KEYS_RU.md`](docs/EXTERNAL_API_KEYS_RU.md)
- KK: [`docs/EXTERNAL_API_KEYS_KK.md`](docs/EXTERNAL_API_KEYS_KK.md)
- EN: [`docs/EXTERNAL_API_KEYS_EN.md`](docs/EXTERNAL_API_KEYS_EN.md)

## Scheduler и «Обновить всё»

```text
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Docker service `geokz-external-sync-scheduler` запускает `python -m scripts.external_sync_scheduler`. PostgreSQL row locking защищает от параллельного `RUNNING`; stale run после configurable timeout становится `FAILED`. Ошибка одного source не отменяет batch для остальных.

Настройки:

```env
GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS=300
GEOKZ_EXTERNAL_SYNC_FAILURE_RETRY_HOURS=6
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

## Нефтегазовые месторождения: normalize → match → review

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=ru&limit=100&offset=0
```

Matching детерминированный. Кандидат остаётся `REVIEW_REQUIRED` до решения эксперта. UI получает stable action descriptors:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Review actions:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

`ExternalEntityLink=VERIFIED` подтверждает связь с внешней записью, но не делает `GeologicalEntity=VERIFIED`. Новый объект создаётся только как `DRAFT`.

## Лицензии на геологическое изучение недр: record-level review

Для `zher_koinauyn_geologiyalyk_zer2/v6` GeoKZ использует более строгую схему. Проверенная карточка ресурса содержит административные сведения о лицензии, но не предоставляет стабильный geological-object/deposit identifier или geometry для безопасного автоматического сопоставления.

Поэтому pipeline заканчивается record-level review:

```text
schema
→ sync
→ RAW
→ process
→ REVIEW_REQUIRED
→ ACCEPTED / REJECTED
```

Нормализация:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Normalizer сохраняет `raw_payload` и отдельно формирует:

- `license_number`;
- `issue_date`;
- `license_type_raw` и deterministic `study_scope_code`;
- `term_raw`;
- `basis_raw`;
- `issuing_authority_raw`;
- `holder_raw`;
- `holder_bin`;
- `source_fields`.

Очередь:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Решения:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` означает только, что эксперт сверил normalized административную запись с upstream payload. Это **не создаёт `ExternalEntityLink`, не создаёт `GeologicalEntity`, не публикует геологический факт и не повышает `VerificationStatus`**.

Если upstream checksum изменился, запись становится `CHANGED`, прежние `reviewed_by`, `reviewed_at`, `review_comment` инвалидируются, и требуется новая проверка. Alembic `20260905_0008` добавляет generic reviewer metadata к `external_records`.

Подробные инструкции:
- RU: [`docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md`](docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md)
- KK: [`docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md`](docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md)
- EN: [`docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md`](docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md)

## Controlled geological vocabularies

GeoKZ хранит canonical dictionaries для `lithology`, `marker_type`, `property_kind`, `unit`, но не уничтожает исходные строки источника. Canonical codes подключены к WellInterval/CoreSample/WellMarker/WellLogCurve/WellTest как отдельный normalization layer. Fuzzy auto-resolution не используется.

## Визуальный корреляционный разрез

```text
POST /api/v1/correlation/wells/view
```

Backend выбирает depth axis `TVDSS → TVD → MD`, отдаёт ordered columns, intervals/markers, `renderable`, готовые `MARKER`/`HORIZON` lines и warnings. Клиент не пересчитывает геологию самостоятельно.

Документы:
- RU: [`docs/CROSS_SECTION_VIEW_CONTRACT_RU.md`](docs/CROSS_SECTION_VIEW_CONTRACT_RU.md)
- KK: [`docs/CROSS_SECTION_VIEW_CONTRACT_KK.md`](docs/CROSS_SECTION_VIEW_CONTRACT_KK.md)
- EN: [`docs/CROSS_SECTION_VIEW_CONTRACT_EN.md`](docs/CROSS_SECTION_VIEW_CONTRACT_EN.md)

## Synthetic demo correlation workflow

```text
POST /api/v1/correlation/demo/workflow
```

`synthetic-correlation-demo-v1` отделён от production wells. Первый вызов возвращает `DISCOVERY`, затем пользователь выбирает reference/compared wells, второй вызов возвращает `CROSS_SECTION_READY`. Invalid selection получает HTTP `422`.

Seed:

```text
python -m scripts.seed_correlation_demo
```

Документы:
- RU: [`docs/DEMO_CORRELATION_WORKFLOW_RU.md`](docs/DEMO_CORRELATION_WORKFLOW_RU.md)
- KK: [`docs/DEMO_CORRELATION_WORKFLOW_KK.md`](docs/DEMO_CORRELATION_WORKFLOW_KK.md)
- EN: [`docs/DEMO_CORRELATION_WORKFLOW_EN.md`](docs/DEMO_CORRELATION_WORKFLOW_EN.md)

## Полезные endpoints

- health live: `/health/live`
- health ready/PostGIS: `/health/ready`
- about: `/api/v1/about?lang=ru`
- Core Dataset status: `/api/v1/core-dataset/status`
- Core Dataset install/dry-run: `/api/v1/core-dataset/install`
- help: `/api/v1/help/topics?lang=ru`
- external sources: `/api/v1/integrations/sources`
- scheduler: `/api/v1/integrations/scheduler/status`
- Update All: `/api/v1/integrations/sync-all`
- Kazakhstan catalog: `/api/v1/integrations/kazakhstan/catalog`
- Kazakhstan schema: `/api/v1/integrations/kazakhstan/{code}/schema`
- Well Passport: `/api/v1/wells/{well_id}/passport`
- correlation: `/api/v1/correlation/wells/{reference_well_id}`
- visual cross-section: `/api/v1/correlation/wells/view`
- demo workflow: `/api/v1/correlation/demo/workflow`

## Документация

### Roadmap
- RU: [`docs/PROJECT_PLAN_V0_2.md`](docs/PROJECT_PLAN_V0_2.md)
- KK: [`docs/PROJECT_PLAN_V0_2_KK.md`](docs/PROJECT_PLAN_V0_2_KK.md)
- EN: [`docs/PROJECT_PLAN_V0_2_EN.md`](docs/PROJECT_PLAN_V0_2_EN.md)

### User Guide
- RU: [`docs/USER_GUIDE_RU.md`](docs/USER_GUIDE_RU.md)
- KK: [`docs/USER_GUIDE_KK.md`](docs/USER_GUIDE_KK.md)
- EN: [`docs/USER_GUIDE_EN.md`](docs/USER_GUIDE_EN.md)

### GeoKZ Core Dataset
- RU: [`docs/CORE_DATASET_RU.md`](docs/CORE_DATASET_RU.md)
- KK: [`docs/CORE_DATASET_KK.md`](docs/CORE_DATASET_KK.md)
- EN: [`docs/CORE_DATASET_EN.md`](docs/CORE_DATASET_EN.md)

### Kazakhstan Open Data
- RU: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md)
- KK: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md)
- EN: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md)

### Field review
- RU: [`docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`](docs/KAZAKHSTAN_FIELD_REVIEW_RU.md)
- KK: [`docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`](docs/KAZAKHSTAN_FIELD_REVIEW_KK.md)
- EN: [`docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`](docs/KAZAKHSTAN_FIELD_REVIEW_EN.md)

### License review
- RU: [`docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md`](docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md)
- KK: [`docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md`](docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md)
- EN: [`docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md`](docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md)

### Scheduler / review UI / other contracts
- [`docs/EXTERNAL_SYNC_SCHEDULER_RU.md`](docs/EXTERNAL_SYNC_SCHEDULER_RU.md) + KK/EN;
- [`docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md) + KK/EN;
- [`docs/DOCUMENTATION_POLICY.md`](docs/DOCUMENTATION_POLICY.md);
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md);
- [`docs/WINDOWS_DESKTOP_PLAN.md`](docs/WINDOWS_DESKTOP_PLAN.md);
- [`docs/ABOUT.md`](docs/ABOUT.md).

## Автор

**Sarmuldin Rinat**  
Email: **ura07srr@gmail.com**

Repository: `07Rinat07/GeoKZ`
