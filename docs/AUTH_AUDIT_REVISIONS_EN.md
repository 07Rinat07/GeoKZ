# GeoKZ — authentication, roles, audit and revision history

Contract version: `v0.3`.

## Purpose

GeoKZ separates reading geological information from operations that modify scientific master data or record an expert decision. Authentication is not primarily about hiding public reference data; it ensures that every protected change has a verifiable actor, role, reason and immutable history.

## Roles

- `editor` — creates and edits `Source`, `GeologicalEntity` and `Fact`, but cannot raise `verification_status` above `DRAFT`.
- `expert` — performs scientific review, may move master data to `REVIEWED`/`VERIFIED`, and can decide external review-queue items.
- `admin` — includes expert/editor capabilities, manages local user accounts, installs the bundled Core Dataset, and reads the complete audit log.

Role enforcement is performed by the backend. A UI is not treated as a security boundary.

## First administrator

The first local account is created by the operator on the GeoKZ workstation/server. The password is not accepted as a command-line argument and therefore does not enter shell history:

```text
python -m scripts.auth create-user --username admin --display-name "GeoKZ Administrator" --role admin
```

The command securely prompts for the password twice. Minimum password length is 12 characters. Subsequent accounts can be created by an administrator through the API.

## Login and sessions

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

A successful login returns an opaque bearer token. The token itself is held only by the client; PostgreSQL stores only its SHA-256 hash. Passwords are stored as salted `scrypt-v1` hashes. Session lifetime is configured with:

```env
GEOKZ_AUTH_SESSION_HOURS=12
```

Protected requests use `Authorization: Bearer <token>`. Logout sets `revoked_at`; reuse of that token returns HTTP `401`.

## User management

Administrator only:

```text
POST /api/v1/auth/users
GET  /api/v1/auth/users
```

The API never exposes `password_hash` or bearer-token hashes.

## Scientific master-data writes

Creating or modifying sources, geological entities and facts requires an authenticated session:

```text
POST  /api/v1/sources
PATCH /api/v1/sources/{source_id}
POST  /api/v1/entities
PATCH /api/v1/entities/{entity_id}
POST  /api/v1/facts
PATCH /api/v1/facts/{fact_id}
```

PATCH requires an explicit `change_reason`. For every successful CREATE/UPDATE, GeoKZ writes an audit record and a new immutable snapshot in `master_data_revisions` in the same transaction. Revision numbers advance independently per resource. A PostgreSQL advisory transaction lock prevents concurrent updates from assigning the same revision number.

An `editor` may work with DRAFT data but receives HTTP `403` when attempting to set a non-DRAFT verification status. `expert` and `admin` may perform scientific status elevation; this does not bypass evidence or provenance requirements.

## External review

Review queues require authentication. Decisions `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`, and administrative-license `ACCEPT/REJECT` require the `expert` or `admin` role.

Reviewer identity is derived **only from the authenticated principal**. A legacy `reviewer` field may temporarily be accepted in request bodies for compatibility, but the backend ignores it. A client therefore cannot sign a decision as another person.

When an external record creates a new field, the entity remains `DRAFT`. The same transaction stores a new `GeologicalEntity` revision plus the review audit event. A verified `ExternalEntityLink` still never upgrades the geological entity itself to `VERIFIED` automatically.

## AuditLog

The complete audit log is administrator-only:

```text
GET /api/v1/audit/logs
```

Filters include `action`, `resource_type`, `resource_id`, `limit`, and `offset`. Each audit record keeps an actor snapshot (`actor_username`, `actor_role`), action, resource type/ID, reason, and technical details.

`audit_logs` and `master_data_revisions` are append-only at the PostgreSQL layer. Database triggers reject normal `UPDATE` and `DELETE` operations. This protects history even if application code accidentally attempts to mutate an old audit row. A future user-account deletion can null the actor foreign key while the username/role snapshot remains preserved.

## Revision history

Any authenticated user may read scientific master-data history:

```text
GET /api/v1/audit/revisions/source/{source_id}
GET /api/v1/audit/revisions/geological_entity/{entity_id}
GET /api/v1/audit/revisions/fact/{fact_id}
```

Each revision contains `revision_number`, action, a full JSON snapshot after the change, `change_reason`, actor, and timestamp. Revision history is not an automatic rollback mechanism: restoring an older state should be implemented as a new explicit change producing a new revision so that the audit chain remains intact.

## Core Dataset

`GET /api/v1/core-dataset/status` remains read-only and public. Installation:

```text
POST /api/v1/core-dataset/install
```

requires `admin`. Bundled-manifest and checksum validation remain mandatory. The Core Dataset never gains permission to silently overwrite user/expert verified master data.

## Security notes

Never place bearer tokens or passwords in Git, issues, screenshots, or documentation. Do not pass passwords as CLI arguments. Use HTTPS for remote access. If a token is lost, revoke its server-side session when possible.

This P0 provides a local authentication/RBAC foundation. SSO/OIDC, MFA, password reset, and centralized enterprise identity remain separate future extensions and should not complicate the offline-capable local core prematurely.
