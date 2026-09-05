# GeoKZ — актуальный план развития v0.3+

Статус: `2026-09-05`. Текущий feature-срез: `feature/pyside6-data-review-client-v0.3`.

## Цель

GeoKZ — evidence-based геологическое рабочее окно Казахстана: территория/координата → объекты/месторождения/скважины/сейсмика → паспорта → глубинные данные → корреляция → источники/provenance → экспертная проверка.

Базовая система работает без внешних сервисов. Интернет безопасно обогащает локальную БД, но не переписывает verified master data автоматически.

## Уже слито в main

- FastAPI + PostgreSQL 17/PostGIS 3.5 + async SQLAlchemy + Alembic;
- Territory Explorer, Geological Entity Passport, Well Passport;
- WGS84/projected X/Y, UTM 38N–45N, organization-local CRS registry;
- PostGIS nearby search;
- trajectory, logs, tests, core, seismic, markers;
- safe well correlation и visual cross-section view-model;
- synthetic demo correlation workflow;
- Kazakhstan Open Data connector + schema inspection;
- external scheduler + Update All;
- oil/gas field normalization/matching/review;
- geological study license normalization + record-level review;
- controlled geological vocabularies;
- independently versioned Core Dataset manifest/importer;
- Authentication + RBAC + server-owned reviewer identity;
- append-only `AuditLog` + `MasterDataRevision`;
- Alembic head `20260905_0010`;
- PR #13 `GeoKZ v0.3: authentication, RBAC, audit trail and revisions` squash-merged в `main` как `5d605a3f034343f3349e1fcf1c0b35aa4a153e2d` после green Python + PostgreSQL/PostGIS CI.

## Стабильные backend-контракты

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
POST /api/v1/correlation/wells/view
POST /api/v1/correlation/demo/workflow
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
GET  /api/v1/audit/logs
GET  /api/v1/audit/revisions/{resource_type}/{resource_id}
```

## Текущий P0 — Production PySide6 review/data-source client

Цель: первый production-oriented Windows/desktop слой без прямого доступа к ORM/БД.

В текущей feature-ветке реализуется:

- `GeoKZApiClient` поверх HTTP API;
- bearer token только в памяти процесса;
- login/logout и отображение текущей role;
- PySide6 shell с `QThreadPool/QRunnable`, без блокировки event loop;
- экран «Источники данных» + «Обновить всё»;
- независимый version endpoint:

```text
GET /api/v1/system/versions
```

- отображение Application / Alembic DB schema / bundled Core Dataset / installed Core Dataset / provider version;
- due/running/error/last-success state источников;
- field-review queue только по server-owned action descriptors;
- license record ACCEPT/REJECT;
- RAW + normalized provenance;
- AuditLog/revision viewer;
- contextual help RU/KK/EN;
- `geokz-desktop` entry point;
- unit tests desktop API client/localization;
- PostgreSQL/PostGIS integration test system version contract;
- `DESKTOP_CLIENT_RU/KK/EN.md`.

### Инварианты desktop

- PySide6 не импортирует SQLAlchemy models;
- UI не дублирует `CONFIRM_LINK/REJECT_LINK/MANUAL_LINK/CREATE_DRAFT_FIELD` business rules;
- reviewer identity приходит из authenticated session;
- `ExternalEntityLink=VERIFIED` не делает `GeologicalEntity=VERIFIED`;
- token/password не пишутся в файлы/log/settings;
- network failure не создаёт локальный «успешный» scientific state.

### Merge gate текущего P0

```text
compileall
→ Ruff
→ unit tests
→ PostgreSQL/PostGIS integration
→ README
→ USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ DESKTOP_CLIENT RU/KK/EN
→ exact-head CI green
→ PR
→ PR-CI green на том же SHA
→ squash merge в main
```

## Следующий P0 после desktop merge — Core Dataset update channel

1. Signed manifest/bundle format и verification policy.
2. HTTP download/update channel без arbitrary filesystem import.
3. Download → checksum/signature verify → staging → transactional activation.
4. Сохранение предыдущего installed snapshot для rollback.
5. Явная compatibility policy: application version / Alembic schema / Core Dataset schema/version.
6. Audit каждой install/update/rollback операции через authenticated actor.
7. Не запускать update, если signature/checksum/compatibility не подтверждены.
8. RU/KK/EN UI status для available/current/failed/rollback.

## После Core Dataset update channel

### Расширение официальных Kazakhstan connectors

Каждый новый provider/dataset подключается только после проверки metadata/mapping/license/terms и получает RAW, checksum/diff, typed normalizer, review policy и contract tests.

### Global/open geology context

- USGS Mineral Resources;
- Macrostrat;
- OneGeology/OGC;
- Copernicus observation assets.

Эти sources дополняют контекст, но не получают право молча переписывать master data.

### Следующие desktop domain screens

- Territory Explorer/map;
- Geological Entity Passport;
- Well Passport;
- visual correlation renderer;
- document/evidence viewer;
- позже read-only offline cache.

## Definition of Done

Каждый feature slice проходит:

```text
feature branch
→ code + migrations/contracts
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated docs RU/KK/EN
→ exact-head CI green
→ PR
→ PR-CI green на том же exact head
→ squash merge в main
→ следующая задача
```

Автор: **Sarmuldin Rinat — ura07srr@gmail.com**.
