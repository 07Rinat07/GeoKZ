# GeoKZ — пайдаланушы нұсқаулығы (KK)

Нұсқа: `0.3-dev`.

## Мақсаты
GeoKZ Қазақстан аумағы, кен орны, геологиялық құрылым және ұңғыма туралы деректерді өзінің evidence-based базасынан және рұқсат етілген сыртқы көздерден бір жұмыс терезесінде көрсетеді.

Негізгі workflow: аумақ немесе координата → кен орындары/құрылымдар/ұңғымалар/сейсмика → object passport → well passport → интервалдар, литология, ГИС, керн, сынақ, мұнай/газ/су → көрші ұңғымаларды корреляциялау → дереккөз және evidence.

## Тілдер
Пайдаланушы интерфейсі, help, labels және documentation орыс, қазақ және ағылшын тілдерінде жүргізіледі.

## Координата бойынша іздеу
Geographic енгізу мысалы: `43.652341 / 51.168420`. Үтір де қабылданады.

Projected енгізу: `X=5085125.325`, `Y=711157.665`; `5085125,325 / 711157,665` те жарамды.

Үлкен X/Y үшін бастапқы CRS және axis order міндетті. GeoKZ CRS-ті тек сандар бойынша болжамайды. WGS84/UTM helper бар, ал ұйымның local CRS мәндері confirmed EPSG/WKT/PROJ арқылы persistent registry ішінде сақталады.

## Ұңғыма паспорты және корреляция
Well Passport координата, траектория MD/TVD/TVDSS, интервал, стратиграфия, lithology, reservoir, oil/gas/water, porosity/permeability, logs, tests, core және source/evidence көрсетеді.

Көрші ұңғымалар үшін correlation module реперлерді, горизонттарды және коллекторларды салыстырады. Visual contract:

```text
POST /api/v1/correlation/wells/view
```

Backend бір depth axis таңдайды: `TVDSS → TVD → MD`. Салыстыруға келмейтін мәндер `renderable=false` болып қалады және жалған correlation line салынбайды.

Synthetic end-to-end demo:

```text
POST /api/v1/correlation/demo/workflow
```

`synthetic-correlation-demo-v1` production wells-тан қатаң бөлінген. Workflow `DISCOVERY` → selection → `CROSS_SECTION_READY` сатыларымен жұмыс істейді.

## GeoKZ Core Dataset

GeoKZ қолданбамен бірге тәуелсіз нұсқаланатын baseline dataset береді. Оның нұсқасы application version және Alembic revision мәндерінен бөлек.

Ағымдағы bundled snapshot:

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
```

Bundled және current DB-ге installed күйін көру:

```text
GET /api/v1/core-dataset/status
```

`update_available=true` — bundled manifest installed state-пен сәйкес емес немесе dataset әлі орнатылмаған.

DB-ге жазбас бұрын dry-run:

```text
POST /api/v1/core-dataset/install?dry_run=true&lang=kk
```

Bundled snapshot орнату:

```text
POST /api/v1/core-dataset/install?lang=kk
```

GeoKZ manifest schema, `schema_version`, required files, SHA-256, path traversal protection, payload types, duplicate `external_id`, `geokz-core:` namespace және bundle ішіндегі references мәндерін DB write алдында тексереді. Барлық upsert бір transaction ішінде орындалады; қате болса rollback жасалады және install state жазылмайды.

Бір manifest қайта орнатылса, операция idempotent және `changed=false` қайтарады.

Алғашқы bootstrap әдейі минималды: ішкі metadata жазбасы және boundary geometry бекітпейтін «Қазақстан Республикасы» country-level navigation record бар. Дәлелді source жоқ geological `entities` немесе `facts` ойдан қосылмайды.

Administrator CLI:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Толық нұсқаулық: `docs/CORE_DATASET_KK.md`.

## Сыртқы дереккөздер және жаңарту
GeoKZ сыртқы жазбаны бірден verified master data-ға көшірмейді. Жалпы pipeline:

```text
external API → RAW → checksum/diff → normalization → matching/review → verified master view
```

Kazakhstan Open Data үшін екі ресми ресурс тіркелген:

1. `kz-egov-oil-gas-fields`, `apiUri=stat_kgn_117`, `v10`;
2. `kz-egov-geological-study-licenses`, `apiUri=zher_koinauyn_geologiyalyk_zer2`, `v6`.

Ресурс schema-сы production import алдында тексеріледі:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Барлық sources-ты қолмен жаңарту:

```text
POST /api/v1/integrations/sync-all
```

Scheduler күйі:

```text
GET /api/v1/integrations/scheduler/status
```

Due sources-ты бір рет іске қосу:

```text
POST /api/v1/integrations/scheduler/run-due
```

Periodic scheduler FastAPI worker ішінде жұмыс істемейді; dedicated process және PostgreSQL parallel-run protection қолданылады.

## Мұнай-газ кен орындарын processing/review
RAW field records үшін:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Бұл endpoint атауды existing `GeologicalEntity(object_type="field")` және aliases-пен deterministic түрде салыстырады. Нәтиже автоматты түрде VERIFIED болмайды.

Техникалық review queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

UI/view-model:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

Action codes: `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`. Verified `ExternalEntityLink` geological object-ті автоматты түрде VERIFIED етпейді. Жаңа object тек `DRAFT` болып құрылады.

## Геологиялық зерттеу лицензияларын record-level review

`kz-egov-geological-study-licenses` — әкімшілік лицензиялар тізілімі. Тексерілген `v6` карточкасы stable deposit/geological-object identifier немесе geometry бермейді, сондықтан GeoKZ бұл source үшін кен орнын автоматты түрде link жасамайды.

RAW sync-тен кейін:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Normalizer `raw_payload` мәнін сақтап, бөлек `license_number`, `issue_date`, license type, term, basis, issuing authority, holder, BIN және `source_fields` жасайды. Normalized жазба `REVIEW_REQUIRED` күйіне өтеді және `review.entity_matching=NOT_APPLICABLE` болады.

Review queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Accept:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
```

Reject:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` тек әкімшілік normalized payload сарапшы арқылы тексерілгенін білдіреді. Ол `ExternalEntityLink`, `GeologicalEntity` немесе geological fact жасамайды және `VerificationStatus` көтермейді. Upstream checksum өзгерсе, бұрынғы `reviewed_by`, `reviewed_at`, `review_comment` жарамсыз болып, жаңа review қажет.

Толық нұсқаулық: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md`.

## API key
Нақты `data.egov.kz` API v4 жүктеу үшін key қажет:

```env
GEOKZ_EGOV_API_KEY=СІЗДІҢ_НАҚТЫ_КІЛТІҢІЗ
```

Кілт Git, README, issue, PR, screenshot немесе чатқа енгізілмейді. Толық setup: `docs/EXTERNAL_API_KEYS_KK.md`.

## REST API қысқаша

- `GET /api/v1/about` — application және bundled Core Dataset version;
- `GET /api/v1/core-dataset/status` — bundled/installed Core Dataset state;
- `POST /api/v1/core-dataset/install` — dry-run немесе bundled dataset install;
- `GET /api/v1/integrations/sources` — external source registry;
- `GET /api/v1/integrations/scheduler/status` — scheduler status;
- `POST /api/v1/integrations/sync-all` — Update All;
- `POST /api/v1/integrations/scheduler/run-due` — run due;
- `GET /api/v1/integrations/kazakhstan/catalog` — official Kazakhstan datasets;
- `GET /api/v1/integrations/kazakhstan/{code}/schema` — metadata + mapping;
- `POST /api/v1/integrations/kazakhstan/{code}/sync` — selected source sync;
- `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — field processing;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review` — field review;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` — field review UI contract;
- `POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process` — license normalization;
- `GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records` — license review queue;
- `POST /api/v1/correlation/wells/view` — visual cross-section;
- `POST /api/v1/correlation/demo/workflow` — complete synthetic demo.

## Көмек және қауіпсіздік
UI күрделі CRS, axis order, MD/TVD/TVDSS, Core Dataset, external-data review және correlation әрекеттері үшін contextual hints/wizards көрсетуі тиіс. RAW source wording және provenance сақталады; automation reviewer decision-ді үнсіз алмастырмайды.

Core Dataset туралы толық policy: `docs/CORE_DATASET_KK.md`.

Ағымдағы roadmap: `docs/PROJECT_PLAN_V0_2_KK.md`.
