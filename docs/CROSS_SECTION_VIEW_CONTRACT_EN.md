# GeoKZ — correlation cross-section UI/view-model contract (EN)

## Purpose

The visual-section endpoint is designed for future PySide6/web clients. The backend does not draw graphics; it returns an UI-ready structure containing ordered well columns, one explicit vertical depth scale, markers, interval bands, correlation lines, and warnings for incompatible data.

```text
POST /api/v1/correlation/wells/view
```

The request reuses the existing `WellCorrelationRequest` contract:

```json
{
  "reference_well_id": "UUID",
  "well_ids": ["UUID"],
  "language": "en"
}
```

The existing `POST /api/v1/correlation/wells` endpoint remains unchanged and remains the analytical-difference contract. The view endpoint first calls the same `WellCorrelationService` and only adapts that result into a UI-ready view-model. The visual layer therefore introduces no new geological interpretation.

## Depth scale

`depth_axis` exposes:

- `depth_reference` — one explicit depth reference for the whole section;
- `unit=m`;
- `direction=DOWN`;
- `min_depth_m` and `max_depth_m`;
- `padding_m` for visual space above and below the data.

The depth reference is selected deterministically in this preference order:

1. TVDSS;
2. TVD;
3. MD.

The preference is applied first to already-comparable marker/reservoir differences. If no comparable pair exists, GeoKZ chooses the first available depth reference using the same order. If there is no safely renderable data at all, the response uses a technical TVDSS `0..1` scale, sets `has_renderable_data=false`, and returns `NO_RENDERABLE_DATA`.

GeoKZ never silently converts intervals from MD to TVD/TVDSS without a confirmed trajectory. An interval is rendered only when its `depth_reference` equals `depth_axis.depth_reference`.

For markers, explicit `tvdss_m`, `true_vertical_depth_m`, or `measured_depth_m` values may be used. If the required alternate depth is unavailable, `depth_m` is accepted only when the marker's own `depth_reference` matches the selected scale.

## Well columns

`columns[]` preserves request order: the reference well first, then the selected neighboring wells with duplicates removed.

Each column contains:

- `column_index` — stable layout index;
- `well` — the existing `WellCard`;
- `is_reference`;
- `distance_from_reference_m`;
- `markers[]`;
- `intervals[]`.

Markers and intervals expose `renderable`. If an item cannot safely be placed on the common scale, `renderable=false`, its scale coordinate is `null`, and its original depth reference remains available. The client must not invent a conversion for such data.

## Correlation lines

`correlation_lines[]` already contains line endpoints expressed as column indices and depths on the selected scale.

Stable `kind` values:

```text
MARKER
HORIZON
```

`MARKER` is emitted only from `MarkerDifference(comparable=true)` in the selected depth reference.

`HORIZON` is emitted only from `ReservoirDifference(comparable_thickness=true)` and links the midpoints of the already matched interval bands. It visualizes an existing matched interval pair; it is not a new automatic stratigraphic interpretation.

Each line contains:

- `key` — `marker_code` or horizon name;
- `depth_reference`;
- `from_column_index`, `to_column_index`;
- `from_well_id`, `to_well_id`;
- `from_depth_m`, `to_depth_m`.

Lines remain reference-well based because the current analytical correlation is also reference based. A UI must not derive new neighbor-to-neighbor geological links on its own.

## Warnings

Stable warning codes:

```text
DEPTH_REFERENCE_MISMATCH
NON_COMPARABLE_MARKERS
NON_COMPARABLE_INTERVALS
NO_RENDERABLE_DATA
NO_CORRELATION_LINES
```

`DEPTH_REFERENCE_MISMATCH` means some data for a well remains present in the response but cannot be rendered on the common depth scale.

`NON_COMPARABLE_MARKERS` and `NON_COMPARABLE_INTERVALS` are not HTTP errors. GeoKZ preserves non-comparability as part of the scientific result and deliberately avoids drawing a false line.

`NO_CORRELATION_LINES` means columns/data may still be renderable, but no confirmed comparable pair exists for a connecting line.

Warning text is localized using `language=ru|kk|en`; warning codes remain stable client-facing identifiers.

## Interpretation safety

The view-model changes no verification status, creates no markers/intervals, and publishes no facts. It only visualizes the existing correlation result.

Rules:

- TVDSS/TVD/MD are never silently mixed;
- UNKNOWN depth reference is never treated as compatible;
- missing/incompatible data remains explicit;
- a correlation line exists only for an already comparable pair;
- each marker/interval retains its `VerificationStatus`;
- the visual section does not replace expert geological interpretation.

## PySide6

A future screen should consume the backend contract directly:

1. send selected well IDs and the reference well;
2. build the vertical scale from `depth_axis`;
3. place well columns by `column_index`;
4. draw only items with `renderable=true`;
5. draw connections from `correlation_lines`;
6. display `warnings` and `policy_note`.

PySide6 must not reimplement depth-reference selection or geological correlation pairing.
