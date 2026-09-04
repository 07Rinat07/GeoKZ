# GeoKZ — User Guide (EN)

Version: `0.2-dev`.

## Purpose
GeoKZ combines geological information for a territory, field/deposit, geological structure and well from the verified GeoKZ database and permitted external sources.

Primary workflow: territory or coordinate → fields/structures/wells/seismic → object passport → well passport → intervals, lithology, well logs, core, tests, oil/gas/water → source and evidence.

## Languages
The user interface, vocabularies, object names and user documentation support English, Russian and Kazakh.

## Coordinate search
Geographic input example: `43.652341 / 51.168420`. A comma decimal separator is also accepted.

Projected input example: `X=5085125.325`, `Y=711157.665`. The form `5085125,325 / 711157,665` is also accepted.

Large metric X/Y values require the source coordinate reference system: EPSG, UTM zone, SK-42/Gauss-Kruger or a configured local company CRS. GeoKZ must not guess a CRS from the numbers alone.

## Well passport
The well passport includes coordinates, type/operator/status, dates, total depth, MD/TVD/TVDSS trajectory, geological intervals, stratigraphy, lithology, oil/gas/water indications, porosity/permeability, well logs, tests, flow rates, pressure/temperature, core/samples and related documents.

## Sources and updates
Important values expose provenance and verification status. External data never silently overwrites verified GeoKZ master values. Manual and periodic synchronization are supported, while the local database remains usable offline.

## Hints and assistants
Complex fields use four assistance levels: a short field hint, expanded contextual help, a step-by-step wizard and a diagnostic warning.

Current implementation status: `docs/PROJECT_PLAN_V0_2.md`.
