# GeoKZ — User Guide (EN)

Version: `0.3-dev`.

GeoKZ is an evidence-based geological information system for Kazakhstan. The main workflow is: territory or coordinate → fields, structures, wells and seismic → passports → intervals/logs/core/tests → correlation → primary sources, provenance and expert review.

## Core data rule

An external API, importer or AI does not silently overwrite verified master data. GeoKZ preserves RAW/source wording, normalized values, source, version, checksum and review status. Verifying a link to an external record does not automatically verify the geological entity itself.

## Languages

The user interface and documentation are supported in Russian, Kazakh and English: `ru`, `kk`, `en`.

## Coordinate and CRS search

GeoKZ accepts WGS84 latitude/longitude and projected X/Y. Projected coordinates require a confirmed CRS and axis order. Large X/Y values are never used to guess a CRS. WGS84, UTM 38N–45N and persistent organization-local CRS definitions via EPSG/WKT/PROJ are supported.

PostGIS nearby search measures distances in meters and can return geological objects, fields, wells, intervals and seismic data.

## Well Passport and correlation

Well Passport combines coordinates, MD/TVD/TVDSS trajectory, stratigraphy, lithology, reservoirs, fluids, porosity/permeability, logs, tests, core and seismic links.

Visual correlation:

```text
POST /api/v1/correlation/wells/view
```

The backend selects a compatible depth reference in the order `TVDSS → TVD → MD`. Incompatible depth systems are not connected automatically.

Synthetic end-to-end workflow:

```text
POST /api/v1/correlation/demo/workflow
```

Demo wells are explicitly synthetic and remain isolated from production data.

## GeoKZ Core Dataset

The bundled baseline is versioned independently from the application and Alembic.

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=en
POST /api/v1/core-dataset/install?lang=en
```

The current bundled snapshot is `2026.09.0-bootstrap`, `schema_version=1`. Manifest schema, SHA-256, path traversal, `geokz-core:` namespace, duplicate IDs and internal references are validated before installation. Installation is transactional; reinstalling the same snapshot returns `changed=false`.

## External sources and synchronization

The built-in Kazakhstan Open Data datasets are:

- `kz-egov-oil-gas-fields` → `stat_kgn_117/v10`;
- `kz-egov-geological-study-licenses` → `zher_koinauyn_geologiyalyk_zer2/v6`.

Manual Update All:

```text
POST /api/v1/integrations/sync-all
```

Scheduler state:

```text
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

The scheduler runs as a dedicated process/service, not inside every FastAPI worker. PostgreSQL locking prevents parallel `RUNNING` executions for the same source.

## Oil and gas fields: normalize → match → review

After RAW synchronization:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Technical review queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

UI view contract:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=en&limit=100&offset=0
```

The backend provides `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, `method`, and `path` for `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, and `CREATE_DRAFT_FIELD`. Clients do not duplicate these business rules.

`ExternalEntityLink=VERIFIED` verifies only the relationship to the official external record; it does not make `GeologicalEntity=VERIFIED`. A new entity from an `UNMATCHED` record is created only as `DRAFT`.

## Geological study licenses

Normalizer:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

`ACCEPTED` means only that a normalized administrative record was reviewed against its RAW/upstream payload. It does not create an `ExternalEntityLink`, `GeologicalEntity`, or geological fact.

## Authentication, roles and audit

Sign in:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Roles are `editor`, `expert`, and `admin`. Scientific review decisions require `expert/admin`; `admin` also manages users and can read the complete audit log.

Reviewer identity is derived from the authenticated server session instead of trusting a client-supplied `reviewer` string.

History:

```text
GET /api/v1/audit/logs
GET /api/v1/audit/revisions/{resource_type}/{resource_id}
```

AuditLog and revisions are protected as append-only history at the PostgreSQL layer.

## Production PySide6 Desktop

The desktop client uses the HTTP API only and does not import SQLAlchemy models.

Installation:

```powershell
python -m pip install -e ".[desktop]"
```

Start:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang en
```

or:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang en
```

The Data Sources screen consumes the independent version contract:

```text
GET /api/v1/system/versions
```

It displays application version, database/Alembic schema revision, bundled/installed Core Dataset, provider versions, due/running/error state, and last success/error.

Desktop currently includes:

- login/logout with the bearer token kept only in process memory;
- Data Sources + Update All;
- field review driven by server-owned action descriptors;
- license ACCEPT/REJECT;
- RAW/normalized provenance;
- AuditLog/revision viewer;
- contextual help in RU/KK/EN;
- HTTP work through `QThreadPool/QRunnable` so the Qt event loop is not blocked.

See `docs/DESKTOP_CLIENT_EN.md` and `docs/AUTH_AUDIT_REVISIONS_EN.md` for details.

## data.egov.kz API key

A developer API key is required for real API v4 downloads. Store it only in the local environment:

```env
GEOKZ_EGOV_API_KEY=YOUR_REAL_KEY
```

Do not commit or publish the secret in Git, issues/PRs, documentation, screenshots, or chat. GeoKZ core remains usable without this key.

## Author

**Sarmuldin Rinat — ura07srr@gmail.com**
