# GeoKZ — organization and local CRS registry

## Purpose

GeoKZ persists confirmed organization coordinate systems for production X/Y workflows. This is required when source material uses SK-42/Gauss-Kruger, a company-local grid, a custom projection, or another CRS that cannot be safely inferred from coordinate numbers alone.

Core rule: GeoKZ **does not guess the CRS or axis order**. Before a local system can be selected it must have an exact `EPSG`, `WKT`, or `PROJ` definition, a source reference, and an explicit confirmation.

## Data model

Migration `20260904_0005` adds `organization_crs_definitions`. Each entry stores:

- stable `code`;
- RU/KK/EN names;
- `definition_kind`: `EPSG`, `WKT`, or `PROJ`;
- original `definition`;
- normalized `canonical_wkt`;
- authority name/code when PROJ resolves one;
- `default_axis_order`;
- `source_reference`;
- notes;
- `is_confirmed`, `confirmed_by`, `confirmed_at`, `confirmation_note`;
- `is_active` and timestamps.

`confirmed_by` is currently an explicitly supplied reviewer identifier. Binding it to an authenticated user and full AuditLog is a later security milestone, so this confirmation workflow is not a substitute for organization access control.

## Lifecycle

1. Create the CRS as an unconfirmed registry entry.
2. The backend validates the definition with pyproj/PROJ and verifies that it is a projected CRS.
3. GeoKZ stores the original definition and canonical WKT.
4. A specialist checks `source_reference`, definition, and `axis_order` against coordinate metadata, geodetic documentation, project documentation, or another authoritative source.
5. Perform a separate confirm action.
6. Only an active entry with `is_confirmed=true` is `selectable` and usable through `registered_crs_code`.

Changing the definition, definition kind, `default_axis_order`, or `source_reference` automatically clears the confirmation. The entry must then be reviewed and confirmed again.

## REST API

List registry entries:

```text
GET /api/v1/spatial/crs-definitions?lang=en
```

List only selectable entries:

```text
GET /api/v1/spatial/crs-definitions?lang=en&selectable_only=true
```

Create:

```text
POST /api/v1/spatial/crs-definitions?lang=en
```

```json
{
  "code": "company-grid-01",
  "name_ru": "Локальная сетка предприятия 01",
  "name_kk": "Кәсіпорынның жергілікті торы 01",
  "name_en": "Company local grid 01",
  "definition_kind": "EPSG",
  "definition": "EPSG:32639",
  "default_axis_order": "x_easting_y_northing",
  "source_reference": "Project coordinate-system passport No. ..."
}
```

Edit:

```text
PATCH /api/v1/spatial/crs-definitions/{definition_id}?lang=en
```

Confirm:

```text
POST /api/v1/spatial/crs-definitions/{definition_id}/confirm?lang=en
```

```json
{
  "confirmed_by": "geodesy-reviewer",
  "confirmation_note": "Checked against the project coordinate-system passport"
}
```

## Using a registered CRS in coordinate search

After confirmation, use the stable `registered_crs_code` instead of repeating a long WKT/PROJ definition:

```json
{
  "coordinate": {
    "type": "projected",
    "x": 711157.665,
    "y": 4851250.325,
    "registered_crs_code": "company-grid-01"
  },
  "radius_km": 5,
  "language": "en",
  "limit": 25
}
```

The backend loads the confirmed definition and confirmed `axis_order`, transforms the point to WGS84, and returns `registered_crs_code` in `resolved_coordinate`. Clients do not need to copy the CRS definition into every request.

Direct projected input through `crs` remains supported, but `axis_order` is mandatory in that mode. `crs` and `registered_crs_code` are mutually exclusive.

## Errors and safety

- `404` — registry code does not exist;
- `409` — the entry exists but is unconfirmed or inactive;
- `422` — the definition cannot be parsed by PROJ/pyproj, is a geographic CRS where production X/Y requires a projected CRS, conflicts with the confirmed axis order, or the coordinate payload is invalid.

An SK-42/Gauss-Kruger entry must not be registered merely as “SK-42”. GeoKZ requires the exact zone/projection/datum definition from a confirmed source. The same applies to company-local systems: a familiar name or similar numeric ranges are not evidence of a CRS.

## Invariants

- `source_reference` is required;
- `axis_order` is part of the confirmed CRS definition;
- unconfirmed entries never participate in coordinate transformation;
- confirmation-sensitive edits clear `is_confirmed`;
- canonical WKT is stored for reproducibility;
- local CRS use preserves the original X/Y and provenance;
- the UI must display confirmation status and must not offer unconfirmed entries as selectable systems.
