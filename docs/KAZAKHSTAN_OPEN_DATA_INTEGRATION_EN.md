# GeoKZ — Kazakhstan Open Data / data.egov.kz integration (EN)

Current as of: 2026-09-04.

## 1. Official data.egov.kz terminology

GeoKZ keeps the portal terminology unchanged:

- `apiUri` — the technical dataset index/identifier on `data.egov.kz`;
- `version` — the resource version, for example `v10`;
- `fields` — technical field names of the dataset;
- `labelRu`, `labelKk`, `labelEn` — user-facing field labels from metadata;
- `source` — the JSON API v4 query parameter containing `from`, `size`, `query`, `sort`, and other Elasticsearch query options.

Example GeoKZ resource:

```text
GeoKZ code:  kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

`GeoKZ code` is our stable connector identifier. It never replaces or modifies the official `apiUri`.

## 2. Official REST patterns

For `{apiUri}` and `{version}`:

```text
Metadata:
GET https://data.egov.kz/meta/{apiUri}/{version}

Mapping / field structure:
GET https://data.egov.kz/api/v4/mapping/{apiUri}/{version}

API v4 data:
GET https://data.egov.kz/api/v4/{apiUri}/{version}?source={JSON}

Detailed API:
GET https://data.egov.kz/api/detailed/{apiUri}/{version}?source={JSON}
```

For actual API v4 data retrieval GeoKZ passes the user's API key according to portal requirements. The key is stored only through `GEOKZ_EGOV_API_KEY`.

Official API documentation: `https://data.egov.kz/pages/samples`.

## 3. GeoKZ naming conventions for external resources

### 3.1 `code`

Stable internal GeoKZ slug:

```text
kz-egov-<domain>
```

Examples:

```text
kz-egov-oil-gas-fields
kz-egov-geological-study-licenses
```

Rules:

- lowercase;
- ASCII;
- kebab-case;
- `kz-egov-` prefix for `data.egov.kz`;
- describes the resource meaning;
- does not include the version.

### 3.2 `api_uri`

Stored exactly as the official portal `apiUri`:

```text
stat_kgn_117
zher_koinauyn_geologiyalyk_zer2
```

Do not translate, shorten, or replace it with a GeoKZ name.

### 3.3 `version`

Stored separately without transformation:

```text
v10
v6
```

### 3.4 `record_type`

Normalized GeoKZ type for one record:

```text
oil_gas_field
geological_study_license
```

Rules:

- English;
- lowercase;
- singular;
- snake_case;
- describes one record, not the whole dataset title.

### 3.5 RAW field names

Technical field keys returned by `data.egov.kz` remain unchanged in `raw_payload`. GeoKZ normalized fields are created separately in `normalized_payload` or the domain model.

This preserves provenance and allows reprocessing after mapping changes.

## 4. Correct procedure for adding a new resource

1. Find the official dataset on `data.egov.kz`.
2. Obtain its `apiUri` and current `version`.
3. Inspect metadata:

```text
GET /meta/{apiUri}/{version}
```

4. Inspect mapping:

```text
GET /api/v4/mapping/{apiUri}/{version}
```

5. Verify technical field names and types.
6. Run a small sample query such as `source={"size":5}`.
7. Select a stable identity field; use an alias group if field names may have changed.
8. Add the resource to `app/integrations/kazakhstan_open_data.py`.
9. Add RU/KK/EN names and descriptions.
10. Add registry, metadata/mapping, and parsing tests.
11. Review license/terms and attribution.
12. Register the resource in GeoKZ.
13. Perform the first synchronization into RAW/staging only.
14. After validation, implement normalization/matching/review.

## 5. Inspecting a resource through GeoKZ

Catalog:

```text
GET /api/v1/integrations/kazakhstan/catalog
```

GeoKZ returns:

- `code`;
- `api_uri`;
- `version`;
- `record_type`;
- `metadata_url`;
- `mapping_url`;
- `data_url_template`;
- `detailed_url_template`;
- API-key configuration status;
- registration status.

Inspect official metadata/mapping before ingestion:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Response:

```text
code
api_uri
version
metadata
mapping
```

This endpoint does not normalize or publish data. It only inspects the upstream resource contract.

## 6. Registration and synchronization

Register known resources:

```text
POST /api/v1/integrations/kazakhstan/register
```

Manual synchronization:

```text
POST /api/v1/integrations/kazakhstan/{code}/sync
```

Data flow:

```text
data.egov.kz
  → metadata/mapping validation
  → RAW/staging
  → checksum/diff
  → normalization
  → matching
  → review
  → verified GeoKZ master data
```

## 7. Currently connected resources

### Oil and gas fields of the Republic of Kazakhstan

```text
code:        kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

### Licenses for geological exploration of subsoil

```text
code:        kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

## 8. Compatibility rule

If the portal releases `v11`, GeoKZ keeps the same `code`. The `version`, endpoints, and normalization mapping are updated as needed. Metadata/mapping must be compared and contract tests must pass before switching versions.

## 9. Related documents

- `docs/EXTERNAL_API_KEYS_EN.md` — obtaining and safely storing API keys;
- `docs/USER_GUIDE_EN.md` — user workflow for external sources;
- `docs/PROJECT_PLAN_V0_2_EN.md` — current roadmap;
- `docs/DOCUMENTATION_POLICY.md` — synchronized RU/KK/EN documentation policy.
