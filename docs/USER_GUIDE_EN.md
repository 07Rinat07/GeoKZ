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

After `kz-egov-oil-gas-fields` has been synchronized, the `process` step can be run. GeoKZ normalizes the field name and matches it against existing `field` objects and their aliases. A match is never treated as verified automatically: a `REVIEW_REQUIRED` candidate is created. Ambiguous and unmatched records remain available for expert review.

GeoKZ REST API:

- `GET /api/v1/integrations/kazakhstan/catalog` — list official resources, `api_uri`, version and endpoint templates;
- `GET /api/v1/integrations/kazakhstan/{code}/schema` — fetch official metadata and mapping before ingestion;
- `POST /api/v1/integrations/kazakhstan/register` — register resources in the local GeoKZ database;
- `POST /api/v1/integrations/kazakhstan/{code}/sync` — manually synchronize one resource;
- `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — normalize RAW field records and perform safe matching against GeoKZ entities;
- `GET /api/v1/integrations/sources` — show external sources and latest synchronization state.

The `data.egov.kz` data API requires a developer API key. The key is read only from the `GEOKZ_EGOV_API_KEY` environment variable and must never be committed to Git. Without the key, GeoKZ continues to operate fully on the local database.

Detailed guides:

- `docs/EXTERNAL_API_KEYS_EN.md` — obtaining and configuring the API key;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md` — `apiUri`, mapping, endpoint patterns, processing and GeoKZ resource naming rules.

## Hints and assistants
Complex fields use a short hint, expanded contextual help, step-by-step wizard and diagnostic warning. Contextual help is especially important for CRS, X/Y axis order, MD/TVD/TVDSS, well logs, correlation and external-source configuration.

Current implementation status: `docs/PROJECT_PLAN_V0_2_EN.md`.
