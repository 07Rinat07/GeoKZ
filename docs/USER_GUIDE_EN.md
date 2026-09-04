# GeoKZ — User Guide (EN)

Version: `0.2-dev`.

## Purpose
GeoKZ combines geological information for a territory, field/deposit, geological structure and well from the verified GeoKZ database and permitted external sources.

Primary workflow: territory or coordinate → fields/structures/wells/seismic → object passport → well passport → intervals, lithology, well logs, core, tests, oil/gas/water → nearby-well correlation → source and evidence.

## Languages
The user interface, vocabularies, object names, contextual help and user documentation support English, Russian and Kazakh.

## Coordinate search
Geographic input example: `43.652341 / 51.168420`. A comma decimal separator is also accepted.

Projected input example: `X=5085125.325`, `Y=711157.665`. The form `5085125,325 / 711157,665` is also accepted.

Large metric X/Y values require the source CRS: EPSG, UTM zone, SK-42/Gauss-Kruger or a configured local company CRS. The axis order is explicit as X=Easting/Y=Northing or X=Northing/Y=Easting. GeoKZ never guesses the CRS from numbers alone.

The CRS helper lists WGS84 and UTM zones 38N–45N covering Kazakhstan's longitude range. The longitude hint only narrows the choice; it does not prove the CRS of the source document. SK-42/Gauss-Kruger and company-local systems require a confirmed EPSG/WKT/PROJ definition.

After input, GeoKZ resolves the working point to WGS84 and searches within the selected radius. Results include administrative context, nearby geological objects/fields, drilled wells with distance and known intervals, and nearby or covering seismic surveys.

## Well passport
The well passport includes coordinates, type/operator/status, dates, total depth, MD/TVD/TVDSS trajectory, geological intervals, stratigraphy, lithology, oil/gas/water indications, porosity/permeability, well logs, tests, flow rates, pressure/temperature, core/samples and related documents.

## Cross-well section correlation
After coordinate search, the user selects the wells to compare, chooses one reference well and starts correlation. GeoKZ compares markers, lithology, reservoirs, oil/gas/water, depth, thickness, net pay, porosity and permeability in visual and textual form.

TVDSS is preferred. Incompatible depth references are not connected by an automatic line. Each marker retains its source, interpretation method and verification status.

The GeoKZ demo dataset contains clearly marked synthetic wells for UI/correlation testing only; it is not production geological information.

## Sources and updates
External data never silently overwrites verified GeoKZ master values. Incoming records are stored in the RAW/staging layer first and can then pass normalization, entity matching and expert review.

The current version connects to Kazakhstan's official `data.egov.kz` Open Data portal through API v4. Two geology resources are registered:

1. `kz-egov-oil-gas-fields` — oil and gas fields of the Republic of Kazakhstan (`apiUri=stat_kgn_117`, version `v10`).
2. `kz-egov-geological-study-licenses` — licenses for geological exploration of subsoil (`apiUri=zher_koinauyn_geologiyalyk_zer2`, version `v6`).

GeoKZ stores the official `apiUri` and `version` separately. Before a resource is added or switched to a new version, the upstream field schema is inspected through the portal metadata and mapping endpoints. RAW technical field names are preserved unchanged; GeoKZ normalized fields are created separately.

Sources are registered with a 168-hour automatic update interval (weekly), while manual synchronization is available at any time.

### Update All and scheduled synchronization

To manually refresh every enabled source:

```text
POST /api/v1/integrations/sync-all
```

GeoKZ returns a batch summary plus one result per source. A failure from one provider does not cancel the remaining updates. Results can include `SUCCESS`, `FAILED`, `ALREADY_RUNNING`, `SKIPPED_DISABLED` and `SKIPPED_UNSUPPORTED`.

Scheduler state is available at:

```text
GET /api/v1/integrations/scheduler/status
```

`next_due_at`, `due` and `running_run_id` allow a future PySide6 UI to show when a source will be checked again and whether synchronization is currently running.

The dedicated scheduler process runs only due `AUTOMATIC` sources:

```text
POST /api/v1/integrations/scheduler/run-due
```

In Docker it runs as `geokz-external-sync-scheduler`. FastAPI workers do not host a background scheduler loop. A PostgreSQL row lock prevents two concurrent `RUNNING` runs for the same source. A `RUNNING` row older than the configured timeout is converted to `FAILED`, allowing a later retry.

After `kz-egov-oil-gas-fields` has been synchronized, the `process` step can be run. GeoKZ normalizes the field name and matches it against existing `field` objects and their aliases. A match is never treated as verified automatically: a `REVIEW_REQUIRED` candidate is created. Ambiguous and unmatched records remain available for expert review.

## Expert review of external field records
The technical pending queue is available at:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

A localized UI-ready view-model is available at:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=en&limit=100&offset=0
```

The view response includes the total pending count, pagination state, localized entity names, `entity_verification_status`, candidates and backend-generated action descriptors (`CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`). Each descriptor supplies `enabled`, `disabled_reason`, `required_fields`, `optional_fields` and the exact `path`, so PySide6/web clients do not duplicate backend business rules.

For each record the user can explicitly:

- confirm a proposed link to an existing field;
- reject a candidate and provide a reason;
- manually link the record to another existing `GeologicalEntity(object_type="field")`;
- create a new field only when `matching.status=UNMATCHED`.

Confirming a link changes the `ExternalEntityLink` to `VERIFIED`, but it **does not automatically change the `GeologicalEntity.verification_status`**. A newly created entity always starts as `DRAFT` and must undergo separate geological verification for coordinates, wells, stratigraphy, reservoir data and other facts.

Main review actions:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

A repeated `process` must not silently overwrite reviewer-locked decisions (`VERIFIED`, `REJECTED`, `MANUAL`, `verified_by` or a review comment).

## GeoKZ REST API

- `GET /api/v1/integrations/sources` — external sources and latest synchronization state;
- `GET /api/v1/integrations/scheduler/status` — scheduler due/running/error state;
- `POST /api/v1/integrations/sync-all` — manual Update All;
- `POST /api/v1/integrations/scheduler/run-due` — execute the scheduled-due algorithm once;
- `GET /api/v1/integrations/kazakhstan/catalog` — list official resources, `api_uri`, version and endpoint templates;
- `GET /api/v1/integrations/kazakhstan/{code}/schema` — fetch official metadata and mapping before ingestion;
- `POST /api/v1/integrations/kazakhstan/register` — register resources in the local GeoKZ database;
- `POST /api/v1/integrations/kazakhstan/{code}/sync` — manually synchronize one resource;
- `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — normalize RAW field records and perform safe matching against GeoKZ entities;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review` — list records pending expert review;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` — get the localized UI/view-model review queue contract.

The `data.egov.kz` data API requires a developer API key. The key is read only from the `GEOKZ_EGOV_API_KEY` environment variable and must never be committed to Git. Without the key, GeoKZ continues to operate fully on the local database; the scheduler records a per-source error without stopping the application.

Detailed guides:

- `docs/EXTERNAL_API_KEYS_EN.md` — obtaining and configuring the API key;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md` — `apiUri`, mapping, endpoint patterns, processing and GeoKZ resource naming rules;
- `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md` — confirm/reject/manual-link/create-draft-field review workflow;
- `docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md` — stable review queue contract for PySide6/web clients;
- `docs/EXTERNAL_SYNC_SCHEDULER_EN.md` — scheduler, Update All, due/retry policy and parallel-run protection.

## Hints and assistants
Complex fields use a short hint, expanded contextual help, step-by-step wizard and diagnostic warning. Contextual help is especially important for CRS, X/Y axis order, MD/TVD/TVDSS, well logs, correlation and external-source configuration.

Current implementation status: `docs/PROJECT_PLAN_V0_2_EN.md`.

## Visual correlation cross-section
A backend-owned UI view-model is now available on top of the already computed correlation; clients do not reimplement geological correlation rules:

```text
POST /api/v1/correlation/wells/view
```

The backend selects one common depth scale with `TVDSS → TVD → MD` priority. Markers and intervals that cannot be safely represented on the selected reference are returned with `renderable=false` and are not connected automatically. `correlation_lines` contains ready-to-render `MARKER` and `HORIZON` segments, while `warnings` exposes stable codes including `DEPTH_REFERENCE_MISMATCH`, `NO_RENDERABLE_DATA` and `NO_CORRELATION_LINES`.

Clients must display `VerificationStatus` and warnings, but must not invent depth conversions or new correlation links. Full contract: `docs/CROSS_SECTION_VIEW_CONTRACT_EN.md`.
