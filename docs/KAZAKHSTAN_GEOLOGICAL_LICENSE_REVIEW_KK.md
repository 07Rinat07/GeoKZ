# GeoKZ — жер қойнауын геологиялық зерттеу лицензияларын өңдеу және тексеру (KK)

Күйі: `v0.3`, 2026-09-05.

## Дереккөз

GeoKZ Kazakhstan Open Data ресми ресурсын қолданады:

- GeoKZ code: `kz-egov-geological-study-licenses`;
- ресми `apiUri`: `zher_koinauyn_geologiyalyk_zer2`;
- version: `v6`;
- `record_type`: `geological_study_license`;
- порталдағы dataset owner: Қазақстан Республикасы Өнеркәсіп және құрылыс министрлігінің Геология комитеті;
- 2026-09-05 тексерілген карточкада dataset жарияланған және өзекті, 476 жазба көрсетілген, жаңарту күні — 2026-05-20.

Production sync алдында порталдың ағымдағы metadata және mapping мәліметтерін міндетті түрде тексеріңіз:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/schema
```

GeoKZ техникалық field атауларын тұрақты деп есептемейді. Ресми `apiUri` және `version` бөлек сақталады, ал RAW payload field атауларын өзгертпей сақталады.

## v6 карточкасында расталған пайдаланушы өрістері

Ресми dataset карточкасында әкімшілік лицензиялық мәліметтер көрсетіледі:

1. жер қойнауын пайдалану лицензиясының түрі;
2. лицензияның нөмірі мен күні;
3. лицензия мерзімі;
4. лицензия беру негізі;
5. лицензия берген мемлекеттік орган;
6. лицензия берілген тұлға туралы мәлімет.

Normalizer тек осы әкімшілік мәндерден дәлелді түрде шығарылатын деректерді қалыптастырады: `license_number`, `issue_date`, `license_type_raw`, `study_scope_code`, `term_raw`, `basis_raw`, `issuing_authority_raw`, `holder_raw`, `holder_bin`, `source_fields`. Бастапқы жолдар `raw_payload` ішінде қалады.

## Неге кен орнымен автоматты байланыс жоқ

Тексерілген `v6` карточкасында детерминирленген entity matching үшін жеткілікті тұрақты геологиялық объект/кен орны идентификаторы немесе geometry жоқ. Сондықтан GeoKZ бұл dataset жазбасынан **автоматты `ExternalEntityLink` жасамайды және `GeologicalEntity` құрмайды**.

Лицензия — әкімшілік жазба. Оның болуы кен орны координаталарын, литологияны, қорларды, мұнай-газдылықты, ұңғыма интервалдарын немесе басқа геологиялық interpretation мәндерін өздігінен растауға жеткіліксіз.

## Pipeline

```text
schema → sync → RAW → process → REVIEW_REQUIRED → accept / reject
```

Синхрондау:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/sync
```

Нормалдау:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Сәтті normalizer нәтижесінде жазба `normalization_status=NORMALIZED`, `review.status=PENDING`, `review.entity_matching=NOT_APPLICABLE` және `ExternalRecord.status=REVIEW_REQUIRED` алады.

Егер mapping өзгеріп, лицензия нөмірі/күнін бірмәнді анықтау мүмкін болмаса, GeoKZ мәнді болжамайды. Жазба `REVIEW_REQUIRED` күйінде `normalization_status=ERROR` алады және mapping/normalizer түзетілмейінше оны accept жасауға болмайды.

## Review кезегі

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Жауапта бірге сақталады:

- `raw_payload` — порталдан алынған бастапқы жазба;
- `normalized_payload` — GeoKZ жеке normalized view;
- `status`;
- `reviewed_by`;
- `reviewed_at`;
- `review_comment`.

### Әкімшілік жазбаны қабылдау

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
```

Accept тек бір мағынаны білдіреді: сарапшы normalized әкімшілік көріністің қолжетімді upstream payload-қа сәйкестігін тексерді. `ExternalRecord` `ACCEPTED` болады. Бұл **`GeologicalEntity=VERIFIED` дегенді білдірмейді** және геологиялық факт жарияламайды.

### Жазбаны қабылдамау

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

Reject үшін comment міндетті. Себеп: бүлінген upstream жазбасы, қате extraction, ambiguous mapping немесе қолмен тексеруді қажет ететін басқа ақау болуы мүмкін.

## Upstream өзгерісі

Бұрын өңделген жазба жаңа checksum-пен келсе, sync оны `CHANGED` күйіне ауыстырады. Келесі `process` бұрынғы record-level reviewer шешімін (`reviewed_by`, `reviewed_at`, `review_comment`) тазартып, жазбаны қайта `REVIEW_REQUIRED` етеді. Өзгерген upstream payload үшін бұрынғы адам шешімі автоматты түрде қайта қолданылмайды.

Upstream-та жазба жоғалса, verified GeoKZ мәліметтері hard delete болмауы тиіс: `is_deleted_upstream`/tombstone semantics қолданылады.

## API key

API v4 арқылы нақты деректерді алу үшін портал кілті қажет. Ол тек local environment ішінде сақталады:

```env
GEOKZ_EGOV_API_KEY=СІЗДІҢ_НАҚТЫ_КІЛТІҢІЗ
```

Кілтті Git, documentation, issue, PR немесе screenshot ішіне жариялауға болмайды. Толық нұсқаулық: `docs/EXTERNAL_API_KEYS_KK.md`.

## Provenance және safety ережелері

- Normalizer RAW мәнін қайта жазбайды.
- Лицензия нөміріндегі `№` секілді source notation техникалық Unicode normalization салдарынан өзгермеуі тиіс.
- Content fallback техникалық field атаулары өзгергенде compatibility үшін ғана қолданылады; ресми mapping `/schema` арқылы бәрібір тексеріледі.
- Лицензияны кен орнымен fuzzy/semantic matching жасалмайды.
- ACCEPTED әкімшілік жазба geological object `VerificationStatus` мәнін көтермейді.
- Болашақта лицензияны аумақпен немесе лицензиялық блокпен байланыстыру upstream-та тексерілетін identifier/geometry пайда болғанда және жеке review workflow арқылы ғана іске асырылады.

## Definition of Done

Бұл workflow unit tests, PostgreSQL/PostGIS integration tests, Alembic `20260905_0008`, RU/KK/EN documentation және жасыл exact-head CI/PR-CI болғаннан кейін ғана аяқталған болып саналады.
