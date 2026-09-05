# GeoKZ — geological study license processing and review (EN)

Status: `v0.3`, 2026-09-05.

## Source

GeoKZ uses the official Kazakhstan Open Data resource:

- GeoKZ code: `kz-egov-geological-study-licenses`;
- official `apiUri`: `zher_koinauyn_geologiyalyk_zer2`;
- version: `v6`;
- `record_type`: `geological_study_license`;
- dataset owner shown by the portal: Committee of Geology of the Ministry of Industry and Construction of the Republic of Kazakhstan;
- the dataset card checked on 2026-09-05 is published/current, shows 476 records and an update date of 2026-05-20.

Before production sync, inspect current upstream metadata and mapping through:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/schema
```

GeoKZ does not treat technical field names as permanent. Official `apiUri` and `version` are stored separately and RAW payload field names are preserved exactly as received.

## User-facing fields confirmed on the v6 dataset card

The official card exposes administrative license information:

1. subsoil-use license type;
2. license number and date;
3. license term;
4. basis for issue;
5. issuing government authority;
6. information about the license holder.

The normalizer derives only values supported by those administrative fields: `license_number`, `issue_date`, `license_type_raw`, `study_scope_code`, `term_raw`, `basis_raw`, `issuing_authority_raw`, `holder_raw`, `holder_bin`, and `source_fields`. Original strings remain in `raw_payload`.

## Why there is no automatic field/deposit link

The verified `v6` dataset card does not expose a stable geological-object/deposit identifier or geometry sufficient for deterministic entity matching. GeoKZ therefore **does not create an `ExternalEntityLink` and does not create a `GeologicalEntity` automatically from this dataset**.

A license is an administrative record. Its existence does not by itself verify deposit coordinates, lithology, reserves, hydrocarbons, well intervals, or any other geological interpretation.

## Pipeline

```text
schema → sync → RAW → process → REVIEW_REQUIRED → accept / reject
```

Sync:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/sync
```

Normalization:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

After successful normalization a record receives `normalization_status=NORMALIZED`, `review.status=PENDING`, `review.entity_matching=NOT_APPLICABLE`, and `ExternalRecord.status=REVIEW_REQUIRED`.

If upstream mapping changes and the license number/date cannot be identified unambiguously, GeoKZ does not guess. The record remains `REVIEW_REQUIRED` with `normalization_status=ERROR` and cannot be accepted until the mapping/normalizer is corrected.

## Review queue

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

The response keeps the following together:

- `raw_payload` — original upstream record;
- `normalized_payload` — separate GeoKZ representation;
- `status`;
- `reviewed_by`;
- `reviewed_at`;
- `review_comment`.

### Accept an administrative record

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
```

Acceptance means only that a reviewer checked the normalized administrative representation against the available upstream payload. `ExternalRecord` becomes `ACCEPTED`. It **does not mean `GeologicalEntity=VERIFIED`** and it does not publish a geological fact.

### Reject a record

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

A review comment is mandatory for rejection. Typical reasons include a malformed upstream record, extraction defect, ambiguous mapping, or another problem requiring manual investigation.

## Upstream changes

When a previously processed row arrives with a new checksum, sync marks it `CHANGED`. The next `process` clears the previous record-level decision (`reviewed_by`, `reviewed_at`, `review_comment`) and returns the record to `REVIEW_REQUIRED`. A human decision is never silently carried forward to a changed upstream payload.

An upstream disappearance must not hard-delete verified GeoKZ data; `is_deleted_upstream`/tombstone semantics are used instead.

## API key

Actual API v4 data retrieval requires a portal developer key. Store it only in the local environment:

```env
GEOKZ_EGOV_API_KEY=YOUR_REAL_KEY
```

Never commit the key to Git or put it into documentation, issues, pull requests, screenshots, or chat. See `docs/EXTERNAL_API_KEYS_EN.md`.

## Provenance and safety rules

- The normalizer never rewrites RAW.
- Source notation such as the `№` symbol in a license number must not be changed by technical Unicode normalization.
- Content-based fallback exists only for compatibility when technical field names change; the official mapping is still inspected through `/schema`.
- No fuzzy or semantic matching from a license row to a deposit is performed.
- An ACCEPTED administrative record never upgrades a geological object's `VerificationStatus`.
- Future links between licenses and territories/license blocks require a verifiable upstream identifier or geometry and a separate review workflow.

## Definition of Done

This workflow is complete only after unit tests, PostgreSQL/PostGIS integration tests, Alembic `20260905_0008`, synchronized RU/KK/EN documentation, and green exact-head CI plus PR-CI.
