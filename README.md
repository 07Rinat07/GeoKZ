# GeoKZ v0.2-dev

GeoKZ — доказательная геологическая информационная система Казахстана и единое рабочее окно для информации по территории, месторождению, структуре и скважине.

## Основные возможности проекта

- RU / KK / EN во всём пользовательском продукте;
- территория → объект → скважина → интервал → источник;
- поиск по области/району и координатам;
- ввод geographic latitude/longitude и projected X/Y;
- PostGIS-поиск ближайших скважин, объектов и сейсмики;
- паспорт геологического объекта;
- полный паспорт скважины;
- траектория MD/TVD/TVDSS;
- литология, стратиграфия, коллекторы, нефть/газ/вода;
- ГИС/well logs, испытания, керн;
- 2D/3D seismic catalog;
- корреляция разрезов соседних скважин по реперам и интервалам;
- backend-owned visual cross-section view-model с общей depth scale и готовыми correlation lines;
- evidence/provenance и конфликты источников;
- встроенный GeoKZ Core Dataset + обновляемые внешние источники;
- контекстные подсказки и помощники RU/KK/EN.

## Ключевые правила

- **Evidence-first:** факт и интерпретация прослеживаются до источника.
- **Human-in-the-loop:** внешние API и ИИ не переписывают verified master data автоматически.
- **Offline-capable core:** базовая информация доступна без обязательного интернета.
- **Data provenance:** сохраняются источник, версия набора, дата получения, checksum и RAW payload.
- **GIS-first:** PostgreSQL/PostGIS, далее GeoPackage, OGC API Features и QGIS.
- **Safe depth/CRS handling:** MD/TVD/TVDSS и разные CRS не смешиваются молча.
- **Server-owned review rules:** PySide6/web UI получает готовые action descriptors и не дублирует backend business rules.
- **Server-owned cross-section rendering contract:** клиент отображает готовую depth axis/columns/lines и не придумывает собственные depth conversions или correlation links.
- **Dedicated sync scheduler:** periodic external sync выполняется отдельным process/service, не background loop внутри FastAPI workers.
- **Documentation-as-code:** пользовательские инструкции и roadmap поддерживаются на RU/KK/EN и проверяются CI-контрактом.

## Текущий стек

- Python 3.12;
- FastAPI;
- PostgreSQL 17 + PostGIS 3.5;
- SQLAlchemy 2 async;
- Alembic;
- Pydantic;
- Docker Compose;
- GitHub Actions CI;
- PySide6 запланирован для Windows-клиента.

## Внешние источники

Приоритет интеграции:

1. Kazakhstan Open Data (`data.egov.kz`);
2. другие официальные открытые казахстанские datasets/GIS services;
3. USGS;
4. Macrostrat;
5. OneGeology / OGC;
6. Copernicus;
7. корпоративные WITSML/OSDU endpoints — только при предоставленном организацией доступе.

Внешние данные проходят RAW → checksum/diff → normalization → matching → review → verified master view.

### Официальные Kazakhstan Open Data resources

На этапе `v0.2-dev` подключён реестр:

- `kz-egov-oil-gas-fields` — нефтегазовые месторождения Республики Казахстан;
- `kz-egov-geological-study-licenses` — лицензии на геологическое изучение недр.

GeoKZ использует официальную терминологию `data.egov.kz`:

```text
apiUri   = технический индекс ресурса на портале
version  = версия ресурса, например v10
fields   = технические имена полей
source   = JSON-параметр API v4 для from/size/query/sort
```

Пример:

```text
GeoKZ code:  kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

`GeoKZ code` — стабильный внутренний slug connector-а. Официальный `apiUri` не переводится, не сокращается и хранится отдельно от версии.

Официальные формы endpoint-ов:

```text
GET /meta/{apiUri}/{version}
GET /api/v4/mapping/{apiUri}/{version}
GET /api/v4/{apiUri}/{version}?source={JSON}
GET /api/detailed/{apiUri}/{version}?source={JSON}
```

Перед подключением нового набора GeoKZ должен сначала прочитать metadata и mapping, сверить имена/типы полей, выполнить небольшой sample-запрос, а только затем добавлять normalization/matching.

Каталог GeoKZ:

```text
GET /api/v1/integrations/kazakhstan/catalog
```

Проверка официальных metadata + mapping до импорта:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Регистрация известных источников:

```text
POST /api/v1/integrations/kazakhstan/register
```

Ручная синхронизация конкретного источника:

```text
POST /api/v1/integrations/kazakhstan/{code}/sync
```

### Scheduler и «Обновить всё»

Ручной batch всех включённых источников:

```text
POST /api/v1/integrations/sync-all
```

Состояние due/running/error:

```text
GET /api/v1/integrations/scheduler/status
```

Однократный запуск scheduled-due алгоритма:

```text
POST /api/v1/integrations/scheduler/run-due
```

В Docker Compose scheduler работает отдельным сервисом `geokz-external-sync-scheduler` и запускает `python -m scripts.external_sync_scheduler`. FastAPI workers не содержат фонового scheduler loop. Резервирование `RUNNING` run защищено PostgreSQL row lock; второй параллельный запуск получает `ALREADY_RUNNING`, а stale `RUNNING` после configurable timeout переводится в `FAILED`.

Настройки:

```env
GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS=300
GEOKZ_EXTERNAL_SYNC_FAILURE_RETRY_HOURS=6
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

Ошибка одного source не отменяет batch для остальных; per-source результат содержит `SUCCESS`, `FAILED`, `ALREADY_RUNNING` или один из `SKIPPED_*` status.

Нормализация и безопасное сопоставление нефтегазовых месторождений после RAW-синхронизации:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Этот шаг извлекает название месторождения, сопоставляет его с существующими `GeologicalEntity(object_type="field")` и `EntityName` aliases и создаёт только review-кандидаты. `VERIFIED` master data автоматически не изменяются.

Техническая очередь экспертной проверки:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

Локализованная UI/view-model очередь для PySide6/web:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=ru&limit=100&offset=0
```

View-model возвращает `total_pending`, pagination, локализованные candidate names, отдельный `entity_verification_status`, стабильный `matching_status` и готовые action descriptors. Доступность и форма действия определяются backend полями `enabled`, `disabled_reason`, `required_fields`, `optional_fields` и `path`.

Стабильные action codes:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Поддерживаются явные действия review:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

Ключевое правило: `ExternalEntityLink(status=VERIFIED)` подтверждает связь внешней записи с объектом, но не делает сам `GeologicalEntity` проверенным автоматически. Новый объект из `UNMATCHED` создаётся только как `DRAFT`.

Подробная документация:

- RU: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md)
- KK: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md)
- EN: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md)
- review RU: [`docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`](docs/KAZAKHSTAN_FIELD_REVIEW_RU.md)
- review KK: [`docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`](docs/KAZAKHSTAN_FIELD_REVIEW_KK.md)
- review EN: [`docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`](docs/KAZAKHSTAN_FIELD_REVIEW_EN.md)
- review UI contract RU: [`docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md)
- review UI contract KK: [`docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md)
- review UI contract EN: [`docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md)
- scheduler RU: [`docs/EXTERNAL_SYNC_SCHEDULER_RU.md`](docs/EXTERNAL_SYNC_SCHEDULER_RU.md)
- scheduler KK: [`docs/EXTERNAL_SYNC_SCHEDULER_KK.md`](docs/EXTERNAL_SYNC_SCHEDULER_KK.md)
- scheduler EN: [`docs/EXTERNAL_SYNC_SCHEDULER_EN.md`](docs/EXTERNAL_SYNC_SCHEDULER_EN.md)

### Как получить API-ключ data.egov.kz

Фактическая загрузка данных с `data.egov.kz` требует персонального API-ключа разработчика.

1. Откройте официальный портал: `https://data.egov.kz/`.
2. Авторизуйтесь через доступный способ входа eGov.
3. Перейдите в раздел **«Разработчикам»**.
4. Откройте **«Кабинет разработчика»**.
5. Создайте или скопируйте свой API key.
6. В корне GeoKZ создайте локальный `.env`:

```powershell
Copy-Item .env.example .env
```

7. Запишите ключ только в локальный `.env`:

```env
GEOKZ_EGOV_API_KEY=ВАШ_РЕАЛЬНЫЙ_КЛЮЧ
```

8. Перезапустите GeoKZ API / Docker Compose.
9. В Swagger проверьте `GET /api/v1/integrations/kazakhstan/catalog`: поле `api_key_configured=true` означает, что GeoKZ видит настроенный ключ.
10. Выполните `POST /api/v1/integrations/kazakhstan/register`, затем тестовую синхронизацию нужного набора.

**Безопасность:** реальный ключ нельзя коммитить в Git, вставлять в README/исходный код, issue/PR, публиковать на скриншотах или отправлять в чат. В репозитории остаётся только пустой шаблон `GEOKZ_EGOV_API_KEY=`.

Подробные инструкции:

- RU: [`docs/EXTERNAL_API_KEYS_RU.md`](docs/EXTERNAL_API_KEYS_RU.md)
- KK: [`docs/EXTERNAL_API_KEYS_KK.md`](docs/EXTERNAL_API_KEYS_KK.md)
- EN: [`docs/EXTERNAL_API_KEYS_EN.md`](docs/EXTERNAL_API_KEYS_EN.md)

## Визуальный корреляционный разрез

UI-ready view-model строится поверх существующего `WellCorrelationService`:

```text
POST /api/v1/correlation/wells/view
```

Контракт выбирает одну depth axis с приоритетом `TVDSS → TVD → MD`, возвращает ordered well columns, markers/intervals, `renderable`, готовые `MARKER`/`HORIZON` correlation lines и стабильные warnings. Несовместимые системы глубин не преобразуются и не соединяются молча. Клиент отображает `VerificationStatus` и предупреждения, но не дублирует backend correlation logic.

Полный трёхъязычный контракт:

- RU: [`docs/CROSS_SECTION_VIEW_CONTRACT_RU.md`](docs/CROSS_SECTION_VIEW_CONTRACT_RU.md)
- KK: [`docs/CROSS_SECTION_VIEW_CONTRACT_KK.md`](docs/CROSS_SECTION_VIEW_CONTRACT_KK.md)
- EN: [`docs/CROSS_SECTION_VIEW_CONTRACT_EN.md`](docs/CROSS_SECTION_VIEW_CONTRACT_EN.md)

## Разработка

```powershell
Copy-Item .env.example .env
./scripts/dev.ps1
```

или:

```powershell
docker compose up --build
```

Полезные endpoints:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- live: `http://localhost:8000/health/live`
- ready/PostGIS: `http://localhost:8000/health/ready`
- about: `/api/v1/about?lang=ru`
- help: `/api/v1/help/topics?lang=ru`
- external sources: `/api/v1/integrations/sources`
- external scheduler status: `/api/v1/integrations/scheduler/status`
- external Update All: `/api/v1/integrations/sync-all`
- external run due: `/api/v1/integrations/scheduler/run-due`
- Kazakhstan catalog: `/api/v1/integrations/kazakhstan/catalog`
- Kazakhstan resource schema: `/api/v1/integrations/kazakhstan/{code}/schema`
- Kazakhstan sync: `/api/v1/integrations/kazakhstan/{code}/sync`
- Kazakhstan process/match: `/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process`
- Kazakhstan field review: `/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`
- Kazakhstan review UI contract: `/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`
- well passport: `/api/v1/wells/{well_id}/passport`
- correlation: `/api/v1/correlation/wells/{reference_well_id}`
- visual cross-section view-model: `/api/v1/correlation/wells/view`

## Документация

### Roadmap
- RU: [`docs/PROJECT_PLAN_V0_2.md`](docs/PROJECT_PLAN_V0_2.md)
- KK: [`docs/PROJECT_PLAN_V0_2_KK.md`](docs/PROJECT_PLAN_V0_2_KK.md)
- EN: [`docs/PROJECT_PLAN_V0_2_EN.md`](docs/PROJECT_PLAN_V0_2_EN.md)

### Руководства пользователя
- RU: [`docs/USER_GUIDE_RU.md`](docs/USER_GUIDE_RU.md)
- KK: [`docs/USER_GUIDE_KK.md`](docs/USER_GUIDE_KK.md)
- EN: [`docs/USER_GUIDE_EN.md`](docs/USER_GUIDE_EN.md)

### API-ключи внешних источников
- RU: [`docs/EXTERNAL_API_KEYS_RU.md`](docs/EXTERNAL_API_KEYS_RU.md)
- KK: [`docs/EXTERNAL_API_KEYS_KK.md`](docs/EXTERNAL_API_KEYS_KK.md)
- EN: [`docs/EXTERNAL_API_KEYS_EN.md`](docs/EXTERNAL_API_KEYS_EN.md)

### Интеграция Kazakhstan Open Data
- RU: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md)
- KK: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md)
- EN: [`docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`](docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md)

### Review внешних месторождений
- RU: [`docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`](docs/KAZAKHSTAN_FIELD_REVIEW_RU.md)
- KK: [`docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`](docs/KAZAKHSTAN_FIELD_REVIEW_KK.md)
- EN: [`docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`](docs/KAZAKHSTAN_FIELD_REVIEW_EN.md)

### UI/View-Model contract external review
- RU: [`docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md)
- KK: [`docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md)
- EN: [`docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md`](docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md)

### Scheduler внешней синхронизации
- RU: [`docs/EXTERNAL_SYNC_SCHEDULER_RU.md`](docs/EXTERNAL_SYNC_SCHEDULER_RU.md)
- KK: [`docs/EXTERNAL_SYNC_SCHEDULER_KK.md`](docs/EXTERNAL_SYNC_SCHEDULER_KK.md)
- EN: [`docs/EXTERNAL_SYNC_SCHEDULER_EN.md`](docs/EXTERNAL_SYNC_SCHEDULER_EN.md)

### Visual cross-section contract
- RU: [`docs/CROSS_SECTION_VIEW_CONTRACT_RU.md`](docs/CROSS_SECTION_VIEW_CONTRACT_RU.md)
- KK: [`docs/CROSS_SECTION_VIEW_CONTRACT_KK.md`](docs/CROSS_SECTION_VIEW_CONTRACT_KK.md)
- EN: [`docs/CROSS_SECTION_VIEW_CONTRACT_EN.md`](docs/CROSS_SECTION_VIEW_CONTRACT_EN.md)

### Другие документы
- [`docs/BUSINESS_DOMAIN.md`](docs/BUSINESS_DOMAIN.md) — предметная модель;
- [`docs/I18N.md`](docs/I18N.md) — правила RU/KK/EN;
- [`docs/DOCUMENTATION_POLICY.md`](docs/DOCUMENTATION_POLICY.md) — обязательное сопровождение документации;
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — архитектура;
- [`docs/WINDOWS_DESKTOP_PLAN.md`](docs/WINDOWS_DESKTOP_PLAN.md) — Windows/PySide6;
- [`docs/ABOUT.md`](docs/ABOUT.md) — о проекте.

## Автор

**Sarmuldin Rinat**  
Email: **ura07srr@gmail.com**

Repository: `07Rinat07/GeoKZ`
