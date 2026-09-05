# GeoKZ — User Guide (EN)

Version: `0.3-dev`.

## Purpose
GeoKZ is an evidence-based geological workspace for Kazakhstan. It combines territory, field, structure, well, subsurface, seismic, document, and provenance information from the local GeoKZ database and permitted external sources.

Primary workflow: territory or coordinate → nearby fields/structures/wells/seismic → object passport → well passport → lithology, logs, core, tests, oil/gas/water → neighboring-well correlation → source and evidence.

## Languages
The user interface, help, labels, and user documentation are maintained in Russian, Kazakh, and English.

## Coordinate search
Geographic input example: `43.652341 / 51.168420`. A comma decimal separator is also accepted.

Projected input example: `X=5085125.325`, `Y=711157.665`; `5085125,325 / 711157,665` is also accepted.

Large X/Y values require an explicit source CRS and axis order. GeoKZ never guesses a CRS solely from the numbers. WGS84/UTM helpers are available, while organization-local CRS definitions are stored persistently only after confirmation through EPSG/WKT/PROJ.

## Well Passport and correlation
Well Passport includes coordinates, MD/TVD/TVDSS trajectory, intervals, stratigraphy, lithology, reservoirs, oil/gas/water, porosity/permeability, logs, tests, core, and source/evidence information.

For neighboring wells, the correlation module compares markers, horizons, and reservoirs. The visual API contract is:

```text
POST /api/v1/correlation/wells/view
```

The backend selects one depth axis with priority `TVDSS → TVD → MD`. Non-comparable values are returned as `renderable=false`; the client must not invent correlation lines.

Synthetic end-to-end demo:

```text
POST /api/v1/correlation/demo/workflow
```

Dataset `synthetic-correlation-demo-v1` is strictly isolated from production wells and follows `DISCOVERY` → selection → `CROSS_SECTION_READY`.

## GeoKZ Core Dataset

GeoKZ ships an independently versioned baseline dataset. Its version is separate from both the application version and the Alembic database revision.

Current bundled snapshot:

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
```

Inspect the bundled version and the state installed in the current database:

```text
GET /api/v1/core-dataset/status
```

`update_available=true` means the bundled manifest differs from the installed state or Core Dataset has not yet been installed.

Validate without writing to the database:

```text
POST /api/v1/core-dataset/install?dry_run=true&lang=en
```

Install the bundled snapshot:

```text
POST /api/v1/core-dataset/install?lang=en
```

Before any database write, GeoKZ validates manifest schema, `schema_version`, required files, SHA-256 checksums, path-traversal protection, payload types, duplicate `external_id` values, the `geokz-core:` namespace, and bundle-internal references. All upserts run in one transaction. A failure causes rollback and no installed state is recorded.

Reinstalling the same manifest is idempotent and returns `changed=false`.

The first bootstrap is deliberately minimal: it contains internal metadata and a country-level Republic of Kazakhstan navigation record without asserting a boundary geometry. Geological `entities` and `facts` are not invented without defensible sources.

Administrative CLI:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Detailed guide: `docs/CORE_DATASET_EN.md`.

## External sources and updates
External rows never overwrite verified master data directly. General pipeline:

```text
external API → RAW → checksum/diff → normalization → matching/review → verified master view
```

Two official Kazakhstan Open Data resources are registered:

1. `kz-egov-oil-gas-fields`, `apiUri=stat_kgn_117`, `v10`;
2. `kz-egov-geological-study-licenses`, `apiUri=zher_koinauyn_geologiyalyk_zer2`, `v6`.

Inspect the current upstream resource schema before production import:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Manual Update All:

```text
POST /api/v1/integrations/sync-all
```

Scheduler status:

```text
GET /api/v1/integrations/scheduler/status
```

Run due sources once:

```text
POST /api/v1/integrations/scheduler/run-due
```

The periodic scheduler is a dedicated process, not a loop in FastAPI workers, and PostgreSQL prevents duplicate concurrent runs.

## Oil/gas field processing and review
For synchronized field RAW records:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

The processing step compares the field name deterministically with existing `GeologicalEntity(object_type="field")` names and aliases. It never auto-verifies a match.

Technical queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

UI/view-model queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

Stable actions include `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, and `CREATE_DRAFT_FIELD`. A verified `ExternalEntityLink` does not automatically make the geological object VERIFIED; a newly created object starts as `DRAFT`.

## Geological study license record-level review

`kz-egov-geological-study-licenses` is an administrative license register. The verified `v6` dataset card does not expose a stable deposit/geological-object identifier or geometry sufficient for deterministic linking, so GeoKZ deliberately does not create an automatic deposit link from this source.

After RAW sync run:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

The normalizer preserves `raw_payload` and separately derives license number/date, license type, term, basis, issuing authority, holder, BIN, and `source_fields`. The record becomes `REVIEW_REQUIRED` and `review.entity_matching=NOT_APPLICABLE`.

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

`ACCEPTED` means only that a reviewer checked the normalized administrative record against the available upstream payload. It does not create an `ExternalEntityLink`, does not create a `GeologicalEntity`, does not publish a geological fact, and does not upgrade `VerificationStatus`. If the upstream checksum changes, previous `reviewed_by`, `reviewed_at`, and `review_comment` are invalidated and fresh review is required.

Detailed guide: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md`.

## API key
Actual `data.egov.kz` API v4 retrieval requires a developer key:

```env
GEOKZ_EGOV_API_KEY=YOUR_REAL_KEY
```

Never store the key in Git, README examples with real values, issues, pull requests, screenshots, or chat. Setup instructions: `docs/EXTERNAL_API_KEYS_EN.md`.

## REST API quick reference

- `GET /api/v1/about` — application and bundled Core Dataset version;
- `GET /api/v1/core-dataset/status` — bundled/installed Core Dataset state;
- `POST /api/v1/core-dataset/install` — dry-run or transactional bundled install;
- `GET /api/v1/integrations/sources` — external source registry;
- `GET /api/v1/integrations/scheduler/status` — scheduler state;
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

## Help and safety
The client should show contextual hints/wizards for CRS, axis order, MD/TVD/TVDSS, Core Dataset, external-data review, and correlation. RAW source wording and provenance remain preserved, and automation must never silently replace a reviewer decision.

Detailed Core Dataset policy: `docs/CORE_DATASET_EN.md`.

Current roadmap: `docs/PROJECT_PLAN_V0_2_EN.md`.
