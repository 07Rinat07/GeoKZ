# GeoKZ — интеграция с Kazakhstan Open Data / data.egov.kz (RU)

Актуальность: 2026-09-05.

## 1. Терминология портала

GeoKZ сохраняет официальный контракт `data.egov.kz`:

- `apiUri` — технический идентификатор ресурса;
- `version` — upstream version (`v10`, `v6` и т. д.);
- `fields` — технические upstream field names;
- `labelRu`, `labelKk`, `labelEn` — пользовательские labels из metadata;
- `source` — JSON-параметр API v4 для `from`, `size`, `query`, `sort`;
- `GeoKZ code` — отдельный стабильный внутренний slug;
- `record_type` — внутренний singular snake_case тип одной записи.

Официальные формы:

```text
GET /meta/{apiUri}/{version}
GET /api/v4/mapping/{apiUri}/{version}
GET /api/v4/{apiUri}/{version}?source={JSON}
GET /api/detailed/{apiUri}/{version}?source={JSON}
```

`apiUri` не переводится и не сокращается. `version` не включается в `code`.

## 2. Именование GeoKZ

Для ресурсов портала:

```text
code = kz-egov-<domain>
```

Требования: lowercase, ASCII, kebab-case, смысл ресурса без версии.

`record_type`: lowercase, English, singular, snake_case.

Примеры:

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

## 3. Подключение нового ресурса

1. Найти официальную карточку dataset.
2. Зафиксировать `apiUri` и current `version`.
3. Проверить metadata и mapping.
4. Сверить labels, technical field names и types.
5. Выполнить sample request, например `source={"size":5}`.
6. Определить stable identity field или безопасный deterministic fallback.
7. Проверить license/terms/attribution.
8. Зарегистрировать RU/KK/EN names/descriptions.
9. Сначала импортировать только в RAW/staging.
10. Реализовать typed normalizer.
11. Отдельно определить matching/review semantics; нельзя предполагать, что все datasets соответствуют `GeologicalEntity`.
12. Добавить unit/contract/PostgreSQL integration tests.
13. Обновить RU/KK/EN docs.

GeoKZ inspection endpoint:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Он возвращает `code`, `api_uri`, `version`, `metadata`, `mapping` и ничего не публикует в master data.

## 4. Registry и sync

Каталог:

```text
GET /api/v1/integrations/kazakhstan/catalog
```

Регистрация:

```text
POST /api/v1/integrations/kazakhstan/register
```

Ручной source sync:

```text
POST /api/v1/integrations/kazakhstan/{code}/sync
```

Update All и scheduler:

```text
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Фактическая загрузка API v4 требует `GEOKZ_EGOV_API_KEY`; правила получения и хранения описаны в `docs/EXTERNAL_API_KEYS_RU.md`.

## 5. RAW и provenance

Технические ключи upstream сохраняются в `raw_payload` без переименования. `normalized_payload` создаётся отдельно. Это позволяет повторно обработать записи при изменении mapping и не терять provenance.

Общий pipeline:

```text
data.egov.kz
→ metadata/mapping check
→ RAW
→ checksum/diff
→ typed normalization
→ source-specific matching/review
→ human decision
→ verified master view только там, где это допустимо
```

Upstream deletion хранится как tombstone (`is_deleted_upstream`), а не hard-delete проверенной геологической информации.

## 6. Нефтегазовые месторождения `stat_kgn_117/v10`

Processing:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Normalizer извлекает название месторождения и сохраняет RAW. Matching выполняется с `GeologicalEntity(object_type="field")` и `EntityName` aliases детерминированно.

Безопасность:

- exact/alias match → только `ExternalEntityLink(status=REVIEW_REQUIRED)`;
- несколько кандидатов → `AMBIGUOUS`;
- нет кандидата → `UNMATCHED`;
- reviewer-locked `VERIFIED`/`REJECTED`/`MANUAL` автоматически не перезаписываются;
- новый verified field из внешней строки автоматически не создаётся.

Technical review:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

UI view-model:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

## 7. Лицензии на геологическое изучение недр `zher_koinauyn_geologiyalyk_zer2/v6`

Проверенная карточка `v6` показывает административные сведения: license type, number/date, term, basis, issuing authority и holder. Она не предоставляет стабильный geological-object/deposit identifier или geometry, поэтому field-style matching для этого source не применяется.

Processing:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Normalized fields:

```text
license_number
issue_date
license_type_raw
study_scope_code
term_raw
basis_raw
issuing_authority_raw
holder_raw
holder_bin
source_fields
```

Запись получает `REVIEW_REQUIRED`, а `review.entity_matching=NOT_APPLICABLE`.

Record-level review queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Decisions:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` подтверждает только административное normalized-представление. Оно не создаёт `ExternalEntityLink`, `GeologicalEntity` или геологический факт. Изменённый checksum переводит запись в `CHANGED`; старые `reviewed_by`, `reviewed_at`, `review_comment` инвалидируются и review выполняется заново.

Подробно: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md`.

## 8. Совместимость версий

Если upstream выпускает новую version, GeoKZ сохраняет прежний stable `code`, меняет только `version`/endpoint config после сравнения metadata/mapping и contract tests. Нельзя переключать version без проверки field schema и normalizer assumptions.

## 9. Связанные документы

- `docs/EXTERNAL_API_KEYS_RU.md` — API key;
- `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md` — field matching/review;
- `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md` — license record review;
- `docs/EXTERNAL_SYNC_SCHEDULER_RU.md` — scheduler/Update All;
- `docs/USER_GUIDE_RU.md` — пользовательский workflow;
- `docs/PROJECT_PLAN_V0_2.md` — актуальный roadmap;
- `docs/DOCUMENTATION_POLICY.md` — документационный Definition of Done.
