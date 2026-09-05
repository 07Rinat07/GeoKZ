# GeoKZ — Kazakhstan Open Data / data.egov.kz integration (EN)

Current as of: 2026-09-05.

## 1. Portal terminology

GeoKZ preserves the official `data.egov.kz` contract:

- `apiUri` — technical resource identifier;
- `version` — upstream version;
- `fields` — technical upstream field names;
- `labelRu`, `labelKk`, `labelEn` — metadata labels;
- `source` — API v4 JSON parameter for `from`, `size`, `query`, and `sort`;
- `GeoKZ code` — separate stable internal slug;
- `record_type` — internal singular snake_case type for one record.

Official endpoint forms:

```text
GET /meta/{apiUri}/{version}
GET /api/v4/mapping/{apiUri}/{version}
GET /api/v4/{apiUri}/{version}?source={JSON}
GET /api/detailed/{apiUri}/{version}?source={JSON}
```

The upstream `apiUri` is never translated or shortened. `version` is not embedded in the GeoKZ `code`.

## 2. GeoKZ naming

```text
code = kz-egov-<domain>
```

Rules: lowercase, ASCII, kebab-case, semantic name, no version suffix.

`record_type`: English, lowercase, singular, snake_case.

Examples:

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

## 3. Onboarding a new resource

1. Find the official dataset card.
2. Record `apiUri` and current `version`.
3. Inspect metadata and mapping.
4. Verify technical fields, labels, and types.
5. Run a small sample query such as `source={"size":5}`.
6. Choose a stable identity field or safe deterministic fallback.
7. Review license/terms/attribution.
8. Add RU/KK/EN names and descriptions.
9. Import first into RAW/staging only.
10. Add a typed normalizer.
11. Define source-specific matching/review semantics; never assume every dataset maps to `GeologicalEntity`.
12. Add unit, contract, and PostgreSQL integration tests.
13. Update RU/KK/EN documentation.

GeoKZ schema inspection:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

## 4. Registry, sync, and scheduler

```text
GET  /api/v1/integrations/kazakhstan/catalog
POST /api/v1/integrations/kazakhstan/register
POST /api/v1/integrations/kazakhstan/{code}/sync
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Actual API v4 retrieval requires `GEOKZ_EGOV_API_KEY`; secure setup is documented in `docs/EXTERNAL_API_KEYS_EN.md`.

## 5. RAW and provenance

Upstream technical keys are kept unchanged in `raw_payload`; `normalized_payload` is separate.

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

An upstream disappearance is represented through `is_deleted_upstream`/tombstone semantics rather than hard-deleting verified GeoKZ information.

## 6. Oil/gas fields `stat_kgn_117/v10`

Processing:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

The normalizer extracts the field name and preserves RAW. Deterministic matching uses existing `GeologicalEntity(object_type="field")` names and `EntityName` aliases.

Safety rules:

- exact/alias match → `ExternalEntityLink(status=REVIEW_REQUIRED)` only;
- multiple candidates → `AMBIGUOUS`;
- no candidate → `UNMATCHED`;
- reviewer-locked `VERIFIED`/`REJECTED`/`MANUAL` decisions are not overwritten automatically;
- no verified new field is created automatically.

Review endpoints:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

## 7. Geological study licenses `zher_koinauyn_geologiyalyk_zer2/v6`

The verified v6 dataset card exposes administrative license type, number/date, term, basis, issuing authority, and holder information. It does not expose a stable geological-object/deposit identifier or geometry, so field-style matching is intentionally not used for this source.

Processing:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Normalized fields include `license_number`, `issue_date`, `license_type_raw`, `study_scope_code`, `term_raw`, `basis_raw`, `issuing_authority_raw`, `holder_raw`, `holder_bin`, and `source_fields`.

The record becomes `REVIEW_REQUIRED` with `review.entity_matching=NOT_APPLICABLE`.

Record-level queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Decisions:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` confirms only the normalized administrative representation. It does not create an `ExternalEntityLink`, `GeologicalEntity`, or geological fact. When the upstream checksum changes, the record becomes `CHANGED`; previous `reviewed_by`, `reviewed_at`, and `review_comment` are invalidated and fresh review is required.

Detailed guide: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md`.

## 8. Version compatibility

When upstream publishes a new version, GeoKZ keeps the stable `code`. `version` and endpoint configuration change only after metadata/mapping comparison and contract tests. Never switch versions without validating field-schema and normalizer assumptions.

## 9. Related documentation

- `docs/EXTERNAL_API_KEYS_EN.md`;
- `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`;
- `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md`;
- `docs/EXTERNAL_SYNC_SCHEDULER_EN.md`;
- `docs/USER_GUIDE_EN.md`;
- `docs/PROJECT_PLAN_V0_2_EN.md`;
- `docs/DOCUMENTATION_POLICY.md`.
