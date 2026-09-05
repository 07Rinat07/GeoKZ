# GeoKZ v0.3-dev

GeoKZ — доказательная геологическая информационная система Казахстана и единое рабочее окно для территории, месторождения, структуры, скважины, глубинных данных, источников и экспертной проверки.

**Автор:** Sarmuldin Rinat — ura07srr@gmail.com

## Принципы

- evidence-first: факт/интерпретация прослеживаются до источника;
- human-in-the-loop: external API и AI не переписывают verified master data автоматически;
- offline-capable core: основная БД работает без обязательного интернета;
- independent data lifecycle: application, Alembic schema, Core Dataset и provider versions независимы;
- safe depth/CRS: MD/TVD/TVDSS и разные CRS не смешиваются молча;
- HTTP boundary: desktop/UI не импортирует SQLAlchemy models;
- RU / KK / EN во всём пользовательском продукте и документации.

## Стек

- Python 3.12;
- FastAPI;
- PostgreSQL 17 + PostGIS 3.5;
- SQLAlchemy 2 async;
- Alembic;
- Pydantic;
- httpx;
- PySide6 desktop;
- Docker Compose;
- GitHub Actions CI.

## Запуск backend

```powershell
Copy-Item .env.example .env
./scripts/dev.ps1
```

или:

```powershell
docker compose up --build
```

Swagger: `http://localhost:8000/docs`.

## Production-oriented PySide6 Desktop

Установить desktop optional dependency:

```powershell
python -m pip install -e ".[desktop]"
```

Запустить:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang ru
```

или:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang ru
```

Поддерживаются `ru`, `kk`, `en`.

Desktop реализует:

- login/logout и server-owned RBAC;
- bearer token только в памяти процесса;
- «Источники данных» + «Обновить всё»;
- Application / DB schema / Core Dataset / provider versions;
- due/running/error/last-success status;
- field review по backend action descriptors;
- geological-study-license ACCEPT/REJECT;
- RAW + normalized provenance;
- AuditLog/revision viewer;
- non-blocking HTTP через `QThreadPool/QRunnable`.

Desktop не подключается к PostgreSQL напрямую. Архитектурная граница:

```text
PySide6 → GeoKZApiClient/httpx → FastAPI → application/domain → PostgreSQL/PostGIS
```

## Authentication, RBAC, AuditLog и revisions

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
GET  /api/v1/audit/logs
GET  /api/v1/audit/revisions/{resource_type}/{resource_id}
```

Роли: `editor`, `expert`, `admin`. Reviewer identity определяется authenticated session на сервере. Scientific review decision доступен `expert/admin`.

`AuditLog` и `MasterDataRevision` защищены append-only правилами PostgreSQL. Password/token plaintext не записываются в audit.

## Independent version contract

```text
GET /api/v1/system/versions
```

Возвращает независимо:

- `application_version`;
- `database_schema_version`;
- `bundled_core_dataset_version` + schema version;
- `installed_core_dataset_version` + schema version + install timestamp.

## GeoKZ Core Dataset

Текущий bundled snapshot:

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
namespace:       geokz-core:
```

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=ru
POST /api/v1/core-dataset/install?lang=ru
```

Manifest содержит SHA-256 и compatibility metadata. Перед записью проверяются schema, path traversal, required files, checksums, payload types, duplicate IDs и references. Install transactional и idempotent.

## Spatial и subsurface

GeoKZ поддерживает:

- WGS84 latitude/longitude;
- projected X/Y с обязательной подтверждённой CRS;
- UTM 38N–45N;
- persistent organization-local CRS EPSG/WKT/PROJ;
- PostGIS nearby search в метрах;
- WellTrajectoryPoint;
- WellLogRun/Curve;
- WellTest;
- CoreRun/CoreSample;
- SeismicSurvey/Line/Volume;
- WellMarker;
- controlled vocabularies для lithology/marker/property/unit.

Well Passport агрегирует координаты, trajectory, intervals, lithology/stratigraphy, reservoirs, fluids, porosity/permeability, logs, tests, core, seismic и provenance.

## Корреляция

```text
POST /api/v1/correlation/wells/view
POST /api/v1/correlation/demo/workflow
```

Visual cross-section backend выбирает depth axis `TVDSS → TVD → MD`, отдаёт ordered columns, intervals/markers, renderability, MARKER/HORIZON lines и warnings. UI не пересчитывает геологию самостоятельно.

Synthetic demo dataset изолирован от production wells.

## Kazakhstan Open Data

Built-in datasets:

```text
kz-egov-oil-gas-fields
apiUri=stat_kgn_117
version=v10
record_type=oil_gas_field
```

```text
kz-egov-geological-study-licenses
apiUri=zher_koinauyn_geologiyalyk_zer2
version=v6
record_type=geological_study_license
```

Pipeline:

```text
metadata/mapping
→ RAW
→ checksum/diff
→ typed normalization
→ matching или record-level review
→ human decision
→ verified/master view только по явным правилам
```

### Sync и scheduler

```text
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Scheduler запускается отдельным process/service; PostgreSQL locking предотвращает duplicate RUNNING.

### Oil/gas fields

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

UI получает action descriptors:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

`ExternalEntityLink=VERIFIED` не делает `GeologicalEntity=VERIFIED`. Новый external-derived объект создаётся как `DRAFT`.

### Geological study licenses

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

`ACCEPTED` означает только проверку administrative normalized record относительно RAW payload; geological entity/fact автоматически не создаётся.

## API key data.egov.kz

GeoKZ работает без ключа, но фактический API v4 download требует developer API key:

```env
GEOKZ_EGOV_API_KEY=
```

Реальный ключ хранится только локально/в secret store и никогда не коммитится.

## Документация

Основные пользовательские руководства:

- [`docs/USER_GUIDE_RU.md`](docs/USER_GUIDE_RU.md)
- [`docs/USER_GUIDE_KK.md`](docs/USER_GUIDE_KK.md)
- [`docs/USER_GUIDE_EN.md`](docs/USER_GUIDE_EN.md)

Desktop:

- [`docs/DESKTOP_CLIENT_RU.md`](docs/DESKTOP_CLIENT_RU.md)
- [`docs/DESKTOP_CLIENT_KK.md`](docs/DESKTOP_CLIENT_KK.md)
- [`docs/DESKTOP_CLIENT_EN.md`](docs/DESKTOP_CLIENT_EN.md)

Authentication/audit:

- [`docs/AUTH_AUDIT_REVISIONS_RU.md`](docs/AUTH_AUDIT_REVISIONS_RU.md)
- [`docs/AUTH_AUDIT_REVISIONS_KK.md`](docs/AUTH_AUDIT_REVISIONS_KK.md)
- [`docs/AUTH_AUDIT_REVISIONS_EN.md`](docs/AUTH_AUDIT_REVISIONS_EN.md)

Roadmap:

- [`docs/PROJECT_PLAN_V0_2.md`](docs/PROJECT_PLAN_V0_2.md)
- [`docs/PROJECT_PLAN_V0_2_KK.md`](docs/PROJECT_PLAN_V0_2_KK.md)
- [`docs/PROJECT_PLAN_V0_2_EN.md`](docs/PROJECT_PLAN_V0_2_EN.md)

Дополнительные контракты находятся в `docs/` и проверяются documentation CI.

## Definition of Done

```text
feature branch
→ code/contracts/migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + RU/KK/EN docs
→ exact-head CI green
→ PR
→ PR-CI green на том же SHA
→ squash merge main
→ next roadmap item
```
