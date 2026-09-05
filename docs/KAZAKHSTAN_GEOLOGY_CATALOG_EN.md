# GeoKZ — Kazakhstan official geology catalog expansion (EN)

Contract status: `v0.3`; official resources were reviewed on 2026-09-05.

## Purpose

GeoKZ expands Kazakhstan official data sources in controlled stages. A source first becomes visible and inspectable in the catalog. A typed normalizer, matching policy and review workflow are then implemented. RAW record synchronization is enabled only after those contracts are tested. Publication on `data.egov.kz` by itself never grants a dataset permission to modify trusted GeoKZ master data.

The local GeoKZ database and Core Dataset continue to work without external services and without `GEOKZ_EGOV_API_KEY`.

## Current official catalog

Sources that already have sync/process/review support:

- `kz-egov-oil-gas-fields` → `apiUri=stat_kgn_117`, pinned version `v10`, `record_type=oil_gas_field`;
- `kz-egov-geological-study-licenses` → `apiUri=zher_koinauyn_geologiyalyk_zer2`, pinned version `v6`, `record_type=geological_study_license`.

New official Committee of Geology candidates:

- `kz-egov-solid-mineral-fields` → `apiUri=stat_kgn_118`, solid mineral deposits of the Republic of Kazakhstan;
- `kz-egov-groundwater-fields` → `apiUri=stat_kgn_120`, groundwater deposits of the Republic of Kazakhstan.

Official dataset pages:

```text
https://data.egov.kz/datasets/view?index=stat_kgn_118
https://data.egov.kz/datasets/view?index=stat_kgn_120
```

GeoKZ does **not invent an API version** for these two datasets. Their catalog contract exposes the `LATEST_MAPPING` version policy.

## `LATEST_MAPPING` version policy

Open Data Kazakhstan exposes a dataset mapping endpoint that can be queried without a version. GeoKZ uses that official endpoint to resolve the currently published version:

```text
GET https://data.egov.kz/api/v4/mapping/{apiUri}
```

The connector accepts only mapping keys shaped as `vN`, where `N` is an integer, and selects the greatest numeric version. This makes `v10` correctly newer than `v2`; arbitrary keys such as `preview` are ignored. The resolved version is cached for the connector lifetime and the same value is used consistently for metadata, mapping and data requests.

If the mapping contains no published `vN` version, resolution fails closed with `ExternalSourceProtocolError`. GeoKZ does not guess a version and does not fall through to an unknown endpoint.

Stable existing integrations continue to use the `PINNED` policy: `stat_kgn_117/v10` and `zher_koinauyn_geologiyalyk_zer2/v6` retain their explicitly verified versions.

## Registration and catalog inspection

```text
POST /api/v1/integrations/kazakhstan/register
GET  /api/v1/integrations/kazakhstan/catalog?lang=en
GET  /api/v1/integrations/kazakhstan/{code}/schema
```

`register` creates a local `ExternalDataSource` record for every known official catalog item. Registration does not imply that synchronization is allowed.

`stat_kgn_118` and `stat_kgn_120` intentionally start in the following safe state:

```text
enabled=false
sync_mode=MANUAL
version=LATEST_MAPPING
sync_supported=false
processing_supported=false
```

`source_config` retains `api_uri`, `record_type`, official/metadata/mapping/data URL templates, `version_policy`, `sync_supported` and `processing_supported`.

## Schema inspection before sync is enabled

The endpoints:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-solid-mineral-fields/schema
GET /api/v1/integrations/kazakhstan/kz-egov-groundwater-fields/schema
```

first resolve the published version from mapping and then read versioned metadata and mapping. This inspection does not require an eGov API key. The response returns the **resolved concrete version**, not the `LATEST_MAPPING` sentinel.

This lets GeoKZ implement a typed normalizer against the real current schema rather than hard-coded assumptions. Mapping must be rechecked whenever a normalizer is changed because technical field names in open datasets can evolve.

## Why synchronization is still blocked

An official dataset is not sufficient for safe automatic ingestion. Before a new `record_type` becomes sync-enabled, GeoKZ requires:

1. an explicit schema and identity strategy;
2. a typed normalizer that diagnoses unknown or ambiguous schemas;
3. a provenance-preserving normalized payload;
4. a match policy against existing `GeologicalEntity` records and aliases;
5. a review queue with reviewer-locked decisions;
6. a rule that newly created geological objects remain `DRAFT`;
7. unit and PostgreSQL/PostGIS integration tests;
8. synchronized RU/KK/EN documentation.

Therefore a direct call such as:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-solid-mineral-fields/sync
```

currently returns a controlled configuration error. Even if the local database row is manually enabled, `ExternalConnectorRegistry` will not provide a sync-ready connector until the code contract explicitly changes to `sync_supported=true`.

`Update All` and the scheduler also remain safe: a disabled source is skipped; a catalog-only source forcibly enabled in the database is reported as `SKIPPED_UNSUPPORTED` instead of starting RAW ingestion.

## API key

Metadata, mapping and schema inspection work without a key. Actual API v4 record retrieval requires the local secret:

```env
GEOKZ_EGOV_API_KEY=...
```

The key must never be committed to Git, copied into documentation, written to logs or stored in desktop settings. The PySide6 client does not store the eGov key and communicates only with the GeoKZ API.

## GeoKZ invariants

- upstream `apiUri` is preserved exactly;
- an unknown version is never replaced with a guess;
- RAW and normalized payloads remain separate;
- external data never silently overwrites verified master data;
- `ExternalEntityLink=VERIFIED` does not imply `GeologicalEntity=VERIFIED`;
- a geological object created from review remains `DRAFT`;
- future upstream deletion must become tombstone/inactive state rather than hard-deleting master data;
- an external service is an optional enrichment layer, not a core runtime dependency.

## Next step

After this catalog-only slice, `kz-egov-solid-mineral-fields` (`stat_kgn_118`) is the first candidate to move through the complete pipeline: schema inspection → typed normalizer → matching/review → tests → only then `sync_supported=true`. Groundwater (`stat_kgn_120`) follows as a separate slice so that distinct geological semantics are not mixed into the same review policy.

Author: **Sarmuldin Rinat — ura07srr@gmail.com**.
