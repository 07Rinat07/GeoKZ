# GeoKZ — пайдаланушы нұсқаулығы (KK)

Нұсқа: `0.3-dev`.

GeoKZ — Қазақстанның evidence-based геологиялық ақпараттық жүйесі. Негізгі жол: аумақ немесе координата → кен орындары, құрылымдар, ұңғымалар және сейсмика → паспорттар → интервалдар/ГИС/керн/сынақтар → корреляция → бастапқы дереккөздер, provenance және сараптамалық тексеру.

## Деректердің негізгі ережесі

Сыртқы API, импорт немесе AI verified master data-ны автоматты түрде қайта жазбайды. GeoKZ RAW/source wording, normalized мәндер, source, version, checksum және review status сақтайды. Сыртқы жазбамен байланысты растау геологиялық объектіні автоматты түрде VERIFIED етпейді.

## Тілдер

Пайдаланушы интерфейсі мен құжаттама `ru`, `kk`, `en` тілдерінде қолдау табады.

## Координата және CRS арқылы іздеу

GeoKZ WGS84 latitude/longitude және projected X/Y қабылдайды. Projected coordinates үшін расталған CRS және axis order міндетті. Үлкен X/Y мәндері бойынша CRS автоматты түрде болжанбайды. WGS84, UTM 38N–45N және EPSG/WKT/PROJ арқылы organization-local CRS қолданылады.

PostGIS nearby search қашықтықты метрмен есептейді және geological objects, fields, wells, intervals және seismic нәтижелерін қайтарады.

## Ұңғыма паспорты және корреляция

Well Passport координаталарды, MD/TVD/TVDSS trajectory, stratigraphy, lithology, reservoirs, fluids, porosity/permeability, logs, tests, core және seismic links біріктіреді.

Көрнекі корреляция:

```text
POST /api/v1/correlation/wells/view
```

Backend depth reference-ті `TVDSS → TVD → MD` тәртібімен қауіпсіз таңдайды. Сәйкес емес depth systems автоматты түрде байланыстырылмайды.

Synthetic demo workflow:

```text
POST /api/v1/correlation/demo/workflow
```

Demo wells production data-дан бөлек сақталады.

## GeoKZ Core Dataset

Bundled baseline application және Alembic-тен тәуелсіз version lifecycle қолданады.

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=kk
POST /api/v1/core-dataset/install?lang=kk
```

Ағымдағы bundled snapshot: `2026.09.0-bootstrap`, `schema_version=1`. Орнатуға дейін manifest schema, SHA-256, path traversal, `geokz-core:` namespace, duplicate IDs және internal references тексеріледі. Install transactional; сол snapshot қайта орнатылса `changed=false` қайтарылады.

## Сыртқы дереккөздер және синхрондау

Қазір Kazakhstan Open Data datasets тіркелген:

- `kz-egov-oil-gas-fields` → `stat_kgn_117/v10`;
- `kz-egov-geological-study-licenses` → `zher_koinauyn_geologiyalyk_zer2/v6`.

Барлығын қолмен жаңарту:

```text
POST /api/v1/integrations/sync-all
```

Scheduler күйі:

```text
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Scheduler бөлек process/service ретінде жұмыс істейді. PostgreSQL locking параллель `RUNNING` run-дарды шектейді.

## Мұнай-газ кен орындары: normalize → match → review

RAW sync-тен кейін:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Техникалық queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

UI view contract:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=kk&limit=100&offset=0
```

Backend `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD` үшін `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, `method`, `path` береді. Клиент осы business rules-ты қайта есептемейді.

`ExternalEntityLink=VERIFIED` тек official external record-пен байланысты растайды; ол `GeologicalEntity=VERIFIED` етпейді. `UNMATCHED` жазбадан жаңа объект тек `DRAFT` ретінде жасалады.

## Геологиялық зерттеу лицензиялары

Normalizer:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

`ACCEPTED` тек normalized administrative record RAW/upstream payload-пен салыстырылып тексерілгенін білдіреді. Бұл `ExternalEntityLink`, `GeologicalEntity` немесе geological fact жасамайды.

## Authentication, roles және audit

Кіру:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Roles: `editor`, `expert`, `admin`. Scientific review decision үшін `expert/admin` қажет; `admin` users басқарады және толық audit log оқиды.

Reviewer identity authenticated session арқылы серверде анықталады; client жіберетін `reviewer` мәтініне сенім жоқ.

History:

```text
GET /api/v1/audit/logs
GET /api/v1/audit/revisions/{resource_type}/{resource_id}
```

AuditLog және revisions PostgreSQL деңгейінде append-only қорғанысқа ие.

## Production PySide6 Desktop

Desktop тек HTTP API пайдаланады және SQLAlchemy models импорттамайды.

Орнату:

```powershell
python -m pip install -e ".[desktop]"
```

Іске қосу:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang kk
```

немесе:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang kk
```

«Дереккөздер» экраны independent versions contract қолданады:

```text
GET /api/v1/system/versions
```

Көрсетіледі: Application version, database/Alembic schema revision, bundled/installed Core Dataset, provider versions, due/running/error state және last success/error.

Desktop құрамында:

- login/logout және process memory ішіндегі bearer token;
- Data Sources + Update All;
- server-owned action descriptors бойынша field review;
- license ACCEPT/REJECT;
- RAW/normalized provenance;
- AuditLog/revision viewer;
- RU/KK/EN contextual help;
- Qt event loop-ты блоктамау үшін `QThreadPool/QRunnable`.

Толығырақ: `docs/DESKTOP_CLIENT_KK.md` және `docs/AUTH_AUDIT_REVISIONS_KK.md`.

## data.egov.kz API key

Нақты API v4 download үшін developer API key қажет. Ол тек локалды environment ішінде сақталады:

```env
GEOKZ_EGOV_API_KEY=СІЗДІҢ_НАҚТЫ_КІЛТІҢІЗ
```

Secret Git, issue/PR, documentation немесе screenshot ішінде жарияланбайды. GeoKZ core бұл кілтсіз де жұмыс істейді.

## Автор

**Sarmuldin Rinat — ura07srr@gmail.com**
