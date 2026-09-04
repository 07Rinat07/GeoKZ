# GeoKZ — Demo correlation workflow (EN)

## Purpose

`POST /api/v1/correlation/demo/workflow` provides a safe training path from a coordinate to a ready visual correlation cross-section. It exists to validate UX, API behavior and future PySide6/web clients against synthetic data. It is not a source of production geological facts.

The demo workflow does not introduce a second geological algorithm. It orchestrates existing GeoKZ services:

1. `CoordinateResolver` safely resolves the source coordinate to WGS84;
2. `SpatialSearchService.search_nearby_wells()` performs the PostGIS nearby query;
3. the workflow keeps only wells explicitly registered as members of the demo dataset;
4. the user chooses one reference well and at least one compared well;
5. `WellCrossSectionViewService` builds the same backend-owned cross-section contract exposed by `POST /api/v1/correlation/wells/view`.

## Critical limitation

Dataset `synthetic-correlation-demo-v1` contains synthetic training wells only. The response always exposes `synthetic=true` and a localized warning. The data must not be quoted or reused as real information about fields, reserves, depths, reservoirs or test results.

The workflow deliberately excludes ordinary production wells even when they are inside the same search radius. Demo selection accepts only records that belong to the explicit demo dataset and use the internal demo-well identifier convention.

## Step 1 — discover demo wells

Example request:

```json
{
  "coordinate": {
    "type": "geographic",
    "latitude": 43.652341,
    "longitude": 51.168420
  },
  "radius_km": 5,
  "language": "en",
  "limit": 10
}
```

Endpoint:

```text
POST /api/v1/correlation/demo/workflow
```

On the first call, omit `reference_well_id` and leave `well_ids` empty. The response is in:

```text
stage = DISCOVERY
```

Important fields are:

- `resolved_coordinate` — the safely resolved WGS84 working coordinate;
- `nearby_demo_wells` — synthetic/demo wells within the requested radius, ordered by distance;
- `suggested_reference_well_id` — the nearest demo well as a UI convenience, not a geological conclusion;
- `can_build_cross_section` — `true` when at least two demo wells are available;
- `selection_contract` — the stable backend contract for the next call;
- `warning` — the mandatory synthetic-data warning;
- `selection_note` — localized instructions for selecting wells.

Every item in `nearby_demo_wells` contains `distance_m`, a well card, known intervals, `passport_path`, and explicit `synthetic=true`.

## Step 2 — select wells and build the section

Choose one reference well and at least one compared well from the current `nearby_demo_wells` result. Repeat the same request with the selection:

```json
{
  "coordinate": {
    "type": "geographic",
    "latitude": 43.652341,
    "longitude": 51.168420
  },
  "radius_km": 5,
  "language": "en",
  "limit": 10,
  "reference_well_id": "<reference demo well UUID>",
  "well_ids": [
    "<compared demo well UUID>"
  ]
}
```

A successful response has:

```text
stage = CROSS_SECTION_READY
```

and additionally returns:

- `selection.reference_well_id`;
- `selection.compared_well_ids`;
- `cross_section` — the complete `WellCrossSectionViewResponse`.

The `cross_section` still uses the common depth-reference priority `TVDSS → TVD → MD`, `renderable` flags, `MARKER`/`HORIZON` line segments, warnings, and `VerificationStatus`. The demo orchestration layer does not alter those rules.

## Selection safety

The backend returns HTTP `422` when:

- `reference_well_id` is supplied without any `well_ids`;
- `well_ids` are supplied without `reference_well_id`;
- `well_ids` contains duplicate UUIDs;
- the reference well is also present in `well_ids`;
- any selected well is not one of the demo wells discovered for the current coordinate/radius;
- the input coordinate or CRS cannot be resolved safely.

A client therefore must not treat an old list of demo UUIDs as trusted state across unrelated searches. Each repeated request is revalidated against the current coordinate, radius, limit and local database.

## Why production wells are excluded

The demo workflow is intended to be reproducible. If a real well exists close to the demo coordinate, it must not silently mix synthetic and production data. The backend first resolves the permitted demo well IDs and passes only those IDs into the PostGIS nearby query.

Normal production usage continues to use the general endpoints:

```text
POST /api/v1/spatial/nearby
POST /api/v1/correlation/wells/view
```

The demo endpoint does not replace them.

## Seeding the demo dataset

Create the local synthetic dataset with:

```text
python -m scripts.seed_correlation_demo
```

The current dataset contains four wells, `R1`/`R2` markers and horizon `J-II`. The dataset identifier is centralized as `synthetic-correlation-demo-v1`, so the seed script and runtime workflow use one source of truth.

The seed process is expected to remain idempotent: rerunning it must not duplicate demo entities, wells, markers or intervals.

## UI contract

Recommended PySide6/web flow:

1. collect coordinate and radius;
2. call the demo workflow without a selection;
3. show only `nearby_demo_wells`;
4. highlight `suggested_reference_well_id` only as a UI suggestion;
5. allow exactly one reference well and 1–20 compared wells;
6. call the same endpoint again with the selection;
7. render `cross_section` according to `docs/CROSS_SECTION_VIEW_CONTRACT_EN.md`;
8. keep the synthetic warning visible.

The client must not inject production wells into demo selection, replace the dataset marker, recalculate PostGIS distance, invent depth conversions, or generate correlation links independently of the backend.

## Validation

Definition of Done includes a real PostgreSQL/PostGIS integration test. It validates the complete HTTP path: seed the demo dataset, create a separate production fixture well at the same location, discover only the four demo wells, build a TVDSS cross-section, and reject an attempt to select the production well with HTTP `422`.

This test validates both response behavior and the safety boundary between synthetic demo data and ordinary GeoKZ data.
