# GeoKZ — v0.3+ өзекті даму жоспары

Күйі: `2026-09-05`. Ағымдағы feature: `feature/pyside6-data-review-client-v0.3`.

## Мақсат

GeoKZ — Қазақстанның evidence-based геологиялық жұмыс терезесі: аумақ/координата → объектілер/кен орындары/ұңғымалар/сейсмика → паспорттар → тереңдік деректері → корреляция → source/provenance → сараптамалық review.

Core system сыртқы сервистерсіз жұмыс істейді. Интернет локалды database-ті толықтырады, бірақ verified master data-ны автоматты қайта жазбайды.

## Main ішіне енгізілген

- FastAPI + PostgreSQL 17/PostGIS 3.5 + async SQLAlchemy + Alembic;
- Territory Explorer, Geological Entity Passport, Well Passport;
- WGS84/projected X/Y, UTM 38N–45N, organization-local CRS registry;
- PostGIS nearby search;
- trajectory, logs, tests, core, seismic, markers;
- safe well correlation және visual cross-section view-model;
- synthetic demo correlation workflow;
- Kazakhstan Open Data connector + schema inspection;
- scheduler + Update All;
- oil/gas field normalization/matching/review;
- geological study license normalization + record-level review;
- controlled geological vocabularies;
- independently versioned Core Dataset manifest/importer;
- Authentication + RBAC + server-owned reviewer identity;
- append-only `AuditLog` + `MasterDataRevision`;
- Alembic head `20260905_0010`;
- PR #13 green Python + PostgreSQL/PostGIS CI-ден кейін `main` ішіне `5d605a3f034343f3349e1fcf1c0b35aa4a153e2d` squash commit ретінде енгізілді.

## Тұрақты backend contracts

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

## Ағымдағы P0 — Production PySide6 review/data-source client

Мақсат: ORM/database-ке тікелей қол жеткізбейтін алғашқы production-oriented desktop layer.

Ағымдағы feature ішінде:

- HTTP-only `GeoKZApiClient`;
- bearer token тек process memory ішінде;
- login/logout және current role;
- `QThreadPool/QRunnable` арқылы non-blocking PySide6 shell;
- Data Sources + Update All;
- independent version contract:

```text
GET /api/v1/system/versions
```

- Application / Alembic DB schema / bundled Core Dataset / installed Core Dataset / provider version;
- due/running/error/last-success state;
- field review тек server-owned action descriptors арқылы;
- license ACCEPT/REJECT;
- RAW + normalized provenance;
- AuditLog/revision viewer;
- RU/KK/EN contextual help;
- `geokz-desktop` entry point;
- unit tests және PostgreSQL/PostGIS system-version integration test;
- `DESKTOP_CLIENT_RU/KK/EN.md`.

### Desktop invariants

- PySide6 SQLAlchemy models импорттамайды;
- UI `CONFIRM_LINK/REJECT_LINK/MANUAL_LINK/CREATE_DRAFT_FIELD` rules-ты қайталамайды;
- reviewer identity authenticated session-нан келеді;
- `ExternalEntityLink=VERIFIED` `GeologicalEntity=VERIFIED` етпейді;
- token/password file/log/settings ішіне жазылмайды;
- network failure локалды scientific success state жасамайды.

### Merge gate

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
→ PR-CI green дәл сол SHA
→ squash merge main
```

## Келесі P0 — Core Dataset update channel

1. Signed manifest/bundle және verification policy.
2. HTTP download/update channel, arbitrary filesystem import жоқ.
3. Download → checksum/signature verify → staging → transactional activation.
4. Алдыңғы installed snapshot сақталып, rollback қолдауы.
5. Application/Alembic/Core Dataset compatibility policy.
6. Install/update/rollback операциялары authenticated actor арқылы audit жасайды.
7. Signature/checksum/compatibility расталмаса activation болмайды.
8. RU/KK/EN UI available/current/failed/rollback state көрсетеді.

## Кейінгі бағыттар

- жаңа official Kazakhstan connectors: metadata/mapping/license/terms тексерілгеннен кейін ғана;
- USGS Mineral Resources, Macrostrat, OneGeology/OGC, Copernicus context;
- Territory Explorer/map desktop;
- Geological Entity Passport;
- Well Passport;
- visual correlation renderer;
- document/evidence viewer;
- кейін read-only offline cache.

## Definition of Done

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
→ PR-CI green same exact head
→ squash merge main
→ next task
```

Автор: **Sarmuldin Rinat — ura07srr@gmail.com**.
