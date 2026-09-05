# GeoKZ — Kazakhstan Open Data / data.egov.kz интеграциясы (KK)

Өзектілігі: 2026-09-05.

## 1. Портал терминологиясы

GeoKZ `data.egov.kz` ресми contract мәндерін өзгертпей сақтайды:

- `apiUri` — ресурстың техникалық identifier;
- `version` — upstream нұсқасы;
- `fields` — техникалық field names;
- `labelRu`, `labelKk`, `labelEn` — metadata labels;
- `source` — API v4 үшін `from`, `size`, `query`, `sort` JSON parameter;
- `GeoKZ code` — жеке stable ішкі slug;
- `record_type` — бір жазбаның internal singular snake_case түрі.

Ресми endpoint templates:

```text
GET /meta/{apiUri}/{version}
GET /api/v4/mapping/{apiUri}/{version}
GET /api/v4/{apiUri}/{version}?source={JSON}
GET /api/detailed/{apiUri}/{version}?source={JSON}
```

`apiUri` аударылмайды және қысқартылмайды. `version` `code` ішіне енгізілмейді.

## 2. GeoKZ naming

```text
code = kz-egov-<domain>
```

Талаптар: lowercase, ASCII, kebab-case, version жоқ.

`record_type`: English, lowercase, singular, snake_case.

```text
code:        kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

```text
code:        kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

## 3. Жаңа resource қосу тәртібі

1. Ресми dataset card табу.
2. `apiUri` және current `version` анықтау.
3. Metadata және mapping тексеру.
4. Technical fields/types/labels салыстыру.
5. `source={"size":5}` сияқты sample request жасау.
6. Stable identity field немесе қауіпсіз deterministic fallback белгілеу.
7. License/terms/attribution тексеру.
8. RU/KK/EN names/descriptions қосу.
9. Алғашқы import тек RAW/staging-ке жасалады.
10. Typed normalizer қосылады.
11. Source-specific matching/review semantics анықталады; әр dataset міндетті түрде `GeologicalEntity`-ге сәйкес келеді деп болжауға болмайды.
12. Unit/contract/PostgreSQL integration tests қосылады.
13. RU/KK/EN docs жаңартылады.

Schema inspection:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

## 4. Registry, sync және scheduler

```text
GET  /api/v1/integrations/kazakhstan/catalog
POST /api/v1/integrations/kazakhstan/register
POST /api/v1/integrations/kazakhstan/{code}/sync
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Нақты API v4 download үшін `GEOKZ_EGOV_API_KEY` қажет. Қауіпсіз setup: `docs/EXTERNAL_API_KEYS_KK.md`.

## 5. RAW және provenance

Upstream technical keys `raw_payload` ішінде өзгеріссіз сақталады. `normalized_payload` бөлек құрылады.

```text
data.egov.kz
→ metadata/mapping check
→ RAW
→ checksum/diff
→ typed normalization
→ source-specific matching/review
→ human decision
→ allowed verified master view
```

Upstream deletion verified data-ны hard delete етпейді; `is_deleted_upstream`/tombstone қолданылады.

## 6. `stat_kgn_117/v10` мұнай-газ кен орындары

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Normalizer field name-ді шығарады және RAW сақтайды. Deterministic matching existing `GeologicalEntity(object_type="field")` және `EntityName` aliases арқылы орындалады.

- exact/alias → `ExternalEntityLink(status=REVIEW_REQUIRED)`;
- бірнеше candidate → `AMBIGUOUS`;
- candidate жоқ → `UNMATCHED`;
- reviewer-locked `VERIFIED`/`REJECTED`/`MANUAL` автоматты өзгермейді;
- verified new field автоматты жасалмайды.

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

## 7. `zher_koinauyn_geologiyalyk_zer2/v6` геологиялық зерттеу лицензиялары

Тексерілген v6 dataset card administrative license type, number/date, term, basis, issuing authority және holder мәліметтерін көрсетеді. Stable geological-object/deposit identifier немесе geometry жоқ, сондықтан field-style matching қолданылмайды.

Processing:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Normalized fields: `license_number`, `issue_date`, `license_type_raw`, `study_scope_code`, `term_raw`, `basis_raw`, `issuing_authority_raw`, `holder_raw`, `holder_bin`, `source_fields`.

Жазба `REVIEW_REQUIRED` алады, `review.entity_matching=NOT_APPLICABLE`.

Review queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Decisions:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` тек normalized administrative record тексерілгенін білдіреді. Ол `ExternalEntityLink`, `GeologicalEntity` немесе geological fact жасамайды. Upstream checksum өзгерсе, `CHANGED` күйі бұрынғы `reviewed_by`, `reviewed_at`, `review_comment` шешімін жарамсыз етеді және fresh review талап етеді.

Толық нұсқаулық: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md`.

## 8. Version compatibility

Upstream жаңа version шығарса, GeoKZ stable `code` сақтайды. `version`/endpoint config metadata/mapping салыстыру және contract tests өткеннен кейін ғана өзгереді.

## 9. Байланысты docs

- `docs/EXTERNAL_API_KEYS_KK.md`;
- `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`;
- `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md`;
- `docs/EXTERNAL_SYNC_SCHEDULER_KK.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/PROJECT_PLAN_V0_2_KK.md`;
- `docs/DOCUMENTATION_POLICY.md`.
