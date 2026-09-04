# GeoKZ — External Review Queue UI/View-Model Contract (EN)

Updated: 2026-09-04. Development branch: `feature/external-review-ui-contract-v0.3`.

## Purpose

This contract is intended for the future PySide6 client and other GeoKZ user interfaces. A client must not parse RAW payloads to infer review semantics, calculate which actions are allowed, or reconstruct confirm/reject/manual-link/create-draft-field URLs on its own. The backend returns a typed, localized and directly actionable queue view-model.

Primary endpoint:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=en&limit=100&offset=0
```

Supported languages are `ru`, `kk`, and `en`.

The lower-level `GET .../review` endpoint remains available for technical clients and backward compatibility. User-facing clients should prefer `GET .../review/view`.

## Top-level response

The view-model contains:

- `source_code` — stable internal source code;
- `language` — language used for localized fields;
- `title` — ready-to-render queue title;
- `policy_note` — mandatory verification-policy warning;
- `total_pending` — total number of `REVIEW_REQUIRED` records;
- `returned_count` — records returned in the current page;
- `limit`, `offset` — pagination parameters;
- `has_more` — whether another page is available;
- `records` — review queue records.

Example:

```json
{
  "source_code": "kz-egov-oil-gas-fields",
  "language": "en",
  "title": "Expert review of external oil and gas fields",
  "total_pending": 42,
  "returned_count": 20,
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "records": []
}
```

## Queue record

Each `records` item contains:

- `record_id` — GeoKZ UUID of the external record;
- `external_id` — upstream identifier;
- `display_name` — safe display name;
- `status` — `ExternalRecord` status;
- `matching_status` — normalized matching status;
- `raw_payload` — original upstream record with technical fields preserved;
- `normalized_payload` — GeoKZ normalized interpretation;
- `candidates` — possible links to existing geological entities;
- `actions` — record-level actions.

Stable `matching_status` values are:

```text
CANDIDATE
AMBIGUOUS
UNMATCHED
REVIEWER_LOCKED
UNAVAILABLE
UNKNOWN
```

`UNKNOWN` is a forward-compatible fallback for a new or unrecognized backend matching value. A UI must remain usable instead of failing on a future status.

## Candidate link

Each `candidates` item contains:

- `link_id`;
- `entity_id`;
- `entity_display_name` — localized with EN/RU/KK fallback;
- `entity_verification_status` — verification status of the geological entity itself;
- `match_method`;
- `match_confidence`;
- link `status`;
- `verified_by` and `review_comment` when a reviewer decision already exists;
- candidate-level `actions`.

Critical rule: `entity_verification_status` and the `ExternalEntityLink` status represent different decisions. `ExternalEntityLink=VERIFIED` only confirms that the external record refers to the selected GeoKZ entity. It does not verify coordinates, reserves, stratigraphy, lithology, wells, interpretations or any other geological property of that entity.

## Action descriptor

The UI receives each action as a backend descriptor:

```json
{
  "code": "REJECT_LINK",
  "label": "Reject link",
  "method": "POST",
  "path": "/api/v1/integrations/kazakhstan/.../reject",
  "enabled": true,
  "disabled_reason": null,
  "required_fields": ["reviewer", "comment"],
  "optional_fields": []
}
```

Stable action codes are:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Clients should use `code` for behavior, `label` only for display, `path` as the exact backend endpoint, `enabled` to control availability, and `required_fields`/`optional_fields` to build the action form.

## Action availability rules

`CONFIRM_LINK` and `REJECT_LINK` are enabled only for an unresolved automatic candidate (`REVIEW_REQUIRED` or `AUTO_MATCHED`). If a reviewer decision is already locked, the backend returns `enabled=false` and a localized `disabled_reason`.

`MANUAL_LINK` is available for a pending record and requires `entity_id` and `reviewer`.

`CREATE_DRAFT_FIELD` is enabled only when `matching_status=UNMATCHED`. For `CANDIDATE`, `AMBIGUOUS`, `REVIEWER_LOCKED`, `UNAVAILABLE`, and `UNKNOWN`, the descriptor remains present but disabled. This keeps business rules on the server and lets the UI render a stable layout.

A geological entity created from an external record always starts as `DRAFT`.

## Pagination

The client supplies `limit` from 1 to 200 and `offset >= 0`. The next page should use:

```text
next_offset = offset + returned_count
```

and should be requested only when `has_more=true`.

`total_pending` is calculated by the backend from the actual `ExternalRecord(status=REVIEW_REQUIRED)` queue. A client must not infer the total from the current page length.

## Recommended PySide6 flow

```text
Open External Review screen
  → GET review/view?lang=<current UI language>
  → render records and candidates
  → render backend action descriptors
  → user selects an enabled action
  → collect only required/optional fields
  → POST to action.path
  → after success, refresh the current review/view page
```

A client must not:

- auto-confirm a match;
- convert a VERIFIED source link into a VERIFIED geological entity;
- rebuild endpoint paths when the backend already supplies `path`;
- invoke an action when `enabled=false`;
- hide `policy_note` on the review screen;
- rewrite RAW payloads.

## Compatibility

The view-model is exposed through a separate endpoint and does not change the existing `GET .../review` response. This allows PySide6 and web clients to adopt the new contract incrementally without a breaking change for technical consumers.

When review support is extended to additional external resource types, common queue fields and action descriptor semantics should remain stable. Resource-specific fields should be additive and must not change the meaning of existing action codes.

## Related documents

- `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md` — review business rules;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md` — source integration workflow;
- `docs/USER_GUIDE_EN.md` — end-user workflow;
- `docs/PROJECT_PLAN_V0_2_EN.md` — current roadmap.
