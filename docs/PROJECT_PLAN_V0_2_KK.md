# GeoKZ — v0.3+ өзекті даму жоспары

Күйі: `2026-09-05`, ағымдағы feature: `feature/core-dataset-manifest-importer-v0.3`.

## Мақсат

GeoKZ Қазақстан бойынша evidence-based бір жұмыс терезесі болуы тиіс: аумақ/координата → жақын кен орындары, құрылымдар, ұңғымалар және сейсмика → паспорттар → тереңдік интервалдары, литология, коллекторлар, ГИС, керн және сынақтар → көрші ұңғымаларды корреляциялау → бастапқы sources, provenance, conflicts және expert review.

Қолданба мен пайдаланушы құжаттамасы RU/KK/EN тілдерінде жүргізіледі. Сыртқы API local database-ті байытады, бірақ runtime үшін міндетті емес және verified master data-ны автоматты түрде қайта жазбайды.

## Main-ге іске асырылып біріктірілген

- FastAPI + PostgreSQL 17/PostGIS 3.5 + async SQLAlchemy + Alembic;
- real PostgreSQL/PostGIS CI және Alembic head migration;
- Territory Explorer, Geological Entity Passport, Well Passport;
- geographic/projected coordinates, WGS84/UTM helper, persistent organization CRS registry;
- PostGIS nearby search;
- trajectory/log/test/core/seismic subsurface models;
- WellMarker және қауіпсіз TVDSS/TVD/MD correlation;
- backend-owned cross-section view-model;
- isolated synthetic correlation workflow;
- official Kazakhstan Open Data connector және schema inspection;
- external scheduler + Update All;
- `kz-egov-oil-gas-fields` RAW → normalization → deterministic matching → human review;
- controlled vocabularies және subsurface canonical bindings;
- correlation distance query cartesian-product warning fix;
- `kz-egov-geological-study-licenses` (`zher_koinauyn_geologiyalyk_zer2/v6`) RAW → typed administrative normalization → record-level `REVIEW_REQUIRED → ACCEPTED/REJECTED`, дәлелсіз entity matching жоқ;
- Alembic `20260905_0008` generic external-record reviewer metadata;
- license-review unit және PostgreSQL/PostGIS HTTP integration tests, RU/KK/EN documentation.

Соңғы merged main baseline: PR #11, merge SHA `f70675699aaae53b89eca23f29fefc61bdf78101`.

## Тұрақты іске асырылған API-контракттар

```text
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
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install
```

## Ағымдағы P0 — GeoKZ Core Dataset manifest/importer

Мақсат: қолданбамен бірге жеткізілетін, бірақ Alembic schema migrations және provider sync versions-тан тәуелсіз versioned baseline.

Ағымдағы feature ішінде:

- Alembic `20260905_0009` және `CoreDatasetState`;
- manifest schema v1: `dataset_code`, `dataset_version`, `schema_version`, `created_at`, namespace, dependencies, per-file SHA-256;
- absolute/path traversal protection;
- required-file және checksum validation DB write-тан бұрын;
- sources/regions/entities/facts typed parser;
- duplicate `external_id` validation;
- `geokz-core:` namespace policy;
- bundle-internal reference validation;
- transactional upsert + rollback;
- manifest SHA-256 бойынша idempotence (`changed=false`);
- bundled snapshot `2026.09.0-bootstrap`;
- әдейі minimal bootstrap: internal metadata source + geometry шекарасын бекітпейтін Kazakhstan country navigation record, ойдан шығарылған geological entities/facts жоқ;
- REST status/install API;
- CLI validate/install/status;
- About ішінде bundled Core Dataset version;
- unit tests: checksum/path traversal/schema/duplicate/reference;
- PostgreSQL/PostGIS integration: install/idempotence және rollback;
- `CORE_DATASET_RU/KK/EN.md` құжаттамасы.

API:

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=kk
POST /api/v1/core-dataset/install?lang=kk
```

CLI:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Schema v1 үшін нақты compatibility gate — `schema_version`. `minimum_app_version` әзірге informational metadata; қате SemVer салыстыру логикасы қолданылмайды.

Merge gate: README + USER_GUIDE + roadmap + documentation policy RU/KK/EN, final exact-head `compileall + Ruff + pytest`, PostgreSQL/PostGIS integration, содан кейін сол exact head үшін PR-CI және squash-merge `main`.

## Merge-тен кейінгі келесі P0

### 1. Authentication + AuditLog/Revision

- users/roles: expert/editor/admin;
- review және scientific master data changes үшін audit trail;
- Fact/Entity/geometry/interpretation revision history;
- verified data silent overwrite болмайды;
- administrative write API тек authorization + audit арқылы.

### 2. Production PySide6 review/data-source screens

- «Дереккөздер» + «Барлығын жаңарту»;
- Application / DB schema / Core Dataset / provider versions бөлек көрсету;
- Core Dataset installed/update state;
- due/running/error/status;
- field review server-owned action descriptors арқылы;
- license ACCEPT/REJECT;
- provenance panel және RU/KK/EN contextual help.

### 3. Core Dataset update channel

- signed bundle manifest;
- download/update channel;
- activation-ға дейін staging;
- алдыңғы installed snapshot-қа rollback;
- app/schema/dataset compatibility policy;
- install/rollback audit.

### 4. Kazakhstan official connectors кеңейту

Келесі datasets current metadata/mapping/license/terms тексерілгеннен кейін ғана common provider SDK арқылы қосылады. Әр source RAW, checksum/diff, typed normalizer, review rules және contract tests алуы тиіс.

### 5. Global/open geology context

- USGS Mineral Resources;
- Macrostrat;
- OneGeology/OGC;
- Copernicus observation assets.

Барлық external data source/version/retrieved_at/license/attribution сақтайды. Authority truth дегенді білдірмейді: conflicts қатар сақталып, expert review арқылы шешіледі.

## Әр feature үшін Definition of Done

```text
feature branch
→ code + migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated feature docs RU/KK/EN қажет болса
→ exact-head CI green
→ PR
→ PR-CI green сол head-та
→ squash merge main-ге
→ келесі міндет
```

Негізгі қағида: GeoKZ сыртқы сервистерсіз жұмыс істейді; интернет local evidence-based database-ті қауіпсіз түрде ғана байытады.
