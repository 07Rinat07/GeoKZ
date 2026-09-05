# GeoKZ — Core Dataset update channel (EN)

Contract version: `v0.3`.

## Purpose

GeoKZ Core Dataset is versioned independently from both the application and the database schema. The online update channel accepts only trusted, signed GeoKZ snapshot packages. It is deliberately not an arbitrary local-file import mechanism. GeoKZ remains usable when the update service is unavailable: the bundled Core Dataset and the local PostgreSQL/PostGIS database continue to operate without any network dependency.

Administrative endpoints:

```text
GET  /api/v1/core-dataset/update/status
POST /api/v1/core-dataset/update/apply?dry_run=true&lang=en
POST /api/v1/core-dataset/update/apply?lang=en
POST /api/v1/core-dataset/update/rollback?lang=en
```

Update and rollback operations require the `admin` role. The bundled/local baseline status remains available separately through `/api/v1/core-dataset/status`.

## Trust model

An update descriptor is a JSON document with `channel_schema_version=1`. It contains `dataset_code`, `dataset_version`, `core_dataset_schema_version`, the manifest SHA-256, an HTTPS bundle URL, the bundle SHA-256, publication time, compatibility requirements, `key_id`, and `signature`.

The signature is verified with Ed25519. A GeoKZ runtime stores only trusted **public** keys. A private signing key must never be placed in `.env`, committed to the repository, embedded in the desktop application, or stored in the normal application database.

Configuration:

```env
GEOKZ_CORE_DATASET_UPDATE_MANIFEST_URL=https://updates.example/geokz/core/channel.json
GEOKZ_CORE_DATASET_UPDATE_TRUSTED_PUBLIC_KEYS={"prod-2026":"<base64-raw-ed25519-public-key>"}
GEOKZ_CORE_DATASET_UPDATE_CACHE_DIR=data/runtime/core_dataset_updates
GEOKZ_CORE_DATASET_UPDATE_MAX_BYTES=134217728
```

If the descriptor URL or trusted-key map is missing, the channel reports `DISABLED`. Both descriptor and `bundle_url` must use HTTPS. HTTP redirects are intentionally not followed so an update origin cannot change silently.

## Verification pipeline

The update process is fail-closed:

1. retrieve the descriptor;
2. require a trusted `key_id` and verify the Ed25519 signature over canonical JSON excluding `signature`;
3. run compatibility checks;
4. download the ZIP subject to a maximum size;
5. compare the ZIP SHA-256 against the signed descriptor;
6. extract into staging/cache while rejecting path traversal, absolute paths and symlinks;
7. validate `manifest.json` with the existing Core Dataset validator;
8. compare manifest SHA-256, `dataset_code`, `dataset_version`, and `schema_version` with the signed descriptor;
9. only then enter transactional activation.

A signature, checksum, manifest, archive-safety, or compatibility failure leaves master data unchanged.

## Compatibility gate

Three independent compatibility axes are enforced:

- application: `minimum_app_version` is compared with `PROJECT_VERSION`;
- database: `required_database_revision` must equal the current `alembic_version`;
- Core Dataset format: `core_dataset_schema_version` must equal `CORE_DATASET_SCHEMA_VERSION`.

The current update-state migration is `20260905_0011`. Online updates also require the bundled `geokz-core` baseline to have been installed first; the network channel does not replace bootstrap.

`/api/v1/core-dataset/update/status` reports one of:

- `DISABLED` — channel configuration is absent;
- `FAILED` — the descriptor could not be safely retrieved or verified;
- `CURRENT` — installed manifest matches the signed release;
- `AVAILABLE` — a compatible new release is available;
- `INCOMPATIBLE` — the release is signed but requires a different application/database/Core Dataset schema version.

The response separately exposes `signature_verified`, `compatible`, `compatibility_issues`, installed/available versions, signing `key_id`, and rollback availability.

## Transactional activation

Administrators can run `dry_run=true` first. Dry run performs signature, checksum, ZIP, manifest, and existing Core Dataset validation without activating database changes.

For a real apply operation, the package is downloaded and staged before database write locks are acquired. GeoKZ then acquires a PostgreSQL advisory transaction lock plus a row lock on `CoreDatasetState` and reloads the state. If another process changed the installed manifest while this update was being prepared, activation stops with a conflict and the operation must be retried. Network I/O therefore does not run while holding the row lock.

Before activation, metadata for the previous snapshot is retained: version, schema, manifest SHA-256, source path, file checksums, and item counts. The existing Core Dataset importer then performs its upserts and updates `CoreDatasetState` transactionally.

AuditLog records the authenticated actor, reason `signed_online_update`, source/target versions, manifest SHA-256, bundle SHA-256, `key_id`, and descriptor URL. A client cannot substitute another administrator identity through request data.

## Safe rollback

GeoKZ keeps metadata for one previous snapshot and exposes:

```text
POST /api/v1/core-dataset/update/rollback?lang=en
```

Rollback is not defined as “delete everything introduced by the newer version.” The current Core Dataset importer is intentionally upsert-only because deleting rows could destroy master data that users or experts subsequently enriched.

For that reason, rollback is permitted only when current and previous bundles contain identical `external_id` identity sets separately for sources, regions, entities, and facts. If a release added or removed identities, safe rollback is blocked rather than hard-deleting newer master data.

Before rollback, GeoKZ revalidates both local manifests, the previous manifest SHA-256, and the identity sets. It then acquires advisory/row locks and verifies that `CoreDatasetState` did not change concurrently. A successful rollback is written to AuditLog with reason `safe_rollback`.

If the cached previous manifest is missing or its checksum no longer matches the saved metadata, rollback is rejected as unverifiable.

## Desktop and operations

The PySide6 desktop client never connects to PostgreSQL directly. It uses the GeoKZ HTTP API for update status, apply, and rollback. The UI contract should expose `CURRENT`, `AVAILABLE`, `INCOMPATIBLE`, `FAILED`, the signing `key_id`, compatibility issues, and whether rollback is available.

An `AVAILABLE` release should not be silently installed. Activation is an explicit administrator action. Failure of the online channel must never prevent users from reading already installed geological data.

## Data invariants

The update channel does not weaken normal GeoKZ evidence rules:

- a verified external link does not automatically make `GeologicalEntity=VERIFIED`;
- an update does not silently delete master data;
- provenance and evidence are retained;
- the external network remains an optional enrichment/update layer;
- PostgreSQL/PostGIS remains the source of current local state;
- install/update/rollback history is auditable and bound to an authenticated administrator.
