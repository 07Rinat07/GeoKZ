# GeoKZ Core Dataset — EN

## Purpose

GeoKZ Core Dataset is an independently versioned baseline dataset shipped with the application and installed into PostgreSQL/PostGIS separately from Alembic schema migrations.

The following version streams are intentionally independent:

- GeoKZ application version;
- Alembic revision / database schema;
- GeoKZ Core Dataset version;
- external provider versions and checkpoints.

Content updates must not require Alembic data migrations.

## Current bundled snapshot

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
namespace:       geokz-core:
```

The first bootstrap is deliberately minimal: it contains an internal metadata source record and a country-level navigation record for the Republic of Kazakhstan without asserting a boundary geometry. `entities.jsonl` and `facts.jsonl` are currently empty. GeoKZ does not invent geological production facts merely to populate a baseline.

`geokz-core:source:bootstrap` is Core Dataset technical metadata, not a geological evidence source.

## Manifest and files

The bundle lives under `data/bootstrap/core_dataset/`:

```text
manifest.json
sources.jsonl
regions.geojson
entities.jsonl
facts.jsonl
```

`manifest.json` stores the independent dataset version, `schema_version`, namespace, dependencies, and SHA-256 for every file. Required files must remain inside the bundle root; absolute paths and `..` traversal are rejected.

Before any database write, GeoKZ validates:

1. manifest JSON/Pydantic schema;
2. supported `schema_version`;
3. unique file paths and kinds;
4. path traversal protection;
5. presence of required files;
6. SHA-256 of each file;
7. payload types;
8. unique `external_id` values per record type;
9. required `geokz-core:` namespace;
10. bundle-internal parent/source/entity/related-fact references.

In schema v1, `minimum_app_version` is informational metadata for display and a future compatibility policy. A strict semantic-version gate is not yet applied; the effective v1 compatibility gate is `schema_version`.

## Transactions and rollback

The importer applies all upserts for one bundle in a single SQLAlchemy transaction. `CoreDatasetState` is written only at the end of a successful import. Any exception triggers rollback, so a partially installed baseline is not accepted as valid state.

Reinstalling the same manifest SHA-256 is idempotent: the importer returns `changed=false` and creates no duplicate records.

Core Dataset uses the dedicated `geokz-core:` namespace. This separates managed baseline records from user-created, external, and expert-verified records. The current importer never treats an arbitrary name match as authority to overwrite existing master data.

## REST API

Bundled and installed status:

```text
GET /api/v1/core-dataset/status
```

The response includes `bundled_version`, `schema_version`, manifest SHA-256, dependencies, installed state, and `update_available`.

Validation without database writes:

```text
POST /api/v1/core-dataset/install?dry_run=true&lang=en
```

Install the bundled snapshot:

```text
POST /api/v1/core-dataset/install?lang=en
```

The HTTP endpoint intentionally does not accept an arbitrary filesystem manifest path: the server installs only its trusted bundled snapshot. The CLI is available for administrative work with local bundles.

## CLI

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

For local diagnostics the CLI also accepts an explicit `manifest.json` path as its positional argument.

## About

`GET /api/v1/about` separately exposes:

```text
core_dataset_version
core_dataset_schema_version
```

This is the bundled version, not a claim that it is already installed in the current database. Use `/api/v1/core-dataset/status` for actual database state.

## Rules for future updates

Future snapshots must:

- use a new `dataset_version`;
- preserve stable `external_id` values for the same entity;
- include defensible source/provenance for geological facts;
- pass checksum and reference validation;
- never promote external or AI-derived data to verified master automatically;
- be independently updateable from the `.exe`/application when the schema remains compatible.

Bundle signing, a download/update channel, and rollback to a prior installed version are later phases. Schema v1 already separates the dataset lifecycle from the Alembic lifecycle.
