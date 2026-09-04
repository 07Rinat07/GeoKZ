# GeoKZ — external oil/gas field review and matching (EN)

Current as of: 2026-09-04. Version: `0.2-dev`.

## Purpose

After `kz-egov-oil-gas-fields` (`apiUri=stat_kgn_117`, `v10`) is synchronized, GeoKZ stores records in RAW/staging. The `process` step normalizes the field name and proposes possible matches against existing `GeologicalEntity(object_type="field")` records.

An automatic exact-name or alias match **is not expert verification**. It creates only `ExternalEntityLink(status=REVIEW_REQUIRED)`.

## 1. Read the review queue

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

Parameters: `limit` (1–200) and `offset`. Each item includes RAW payload, normalized payload, record status, and candidate field links.

## 2. Confirm a proposed link

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
```

Example:

```json
{
  "reviewer": "Sarmuldin Rinat",
  "comment": "Confirmed against supporting sources"
}
```

The selected link becomes `VERIFIED`, the ExternalRecord becomes `ACCEPTED`, and other unresolved automatic candidates for that record become `REJECTED`. The external API does not overwrite the existing GeologicalEntity.

If another `VERIFIED` link already exists, GeoKZ refuses to create a second verified association and requires a separate revision procedure.

## 3. Reject a candidate

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
```

Both `reviewer` and `comment` are required. Rejecting one candidate does not automatically close the record if manual linking or further review is still needed.

## 4. Manually link to an existing field

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
```

```json
{
  "entity_id": "existing GeologicalEntity UUID",
  "reviewer": "Sarmuldin Rinat",
  "comment": "Registry name differs from the working field name"
}
```

GeoKZ accepts only `object_type=field` for this resource. The association becomes `match_method=MANUAL`, `status=VERIFIED`; the linked GeologicalEntity keeps its own existing `verification_status`.

## 5. Create a new field from an UNMATCHED record

Only a record with `matching.status=UNMATCHED` may explicitly create a new object:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

Example:

```json
{
  "reviewer": "Sarmuldin Rinat",
  "comment": "Create a card for further geological verification",
  "name_ru": "Название",
  "name_kk": "Атауы",
  "name_en": "Name"
}
```

Critical rule: the new `GeologicalEntity` is created **only as `DRAFT`**. A verified link to an official registry record does not verify the geological object itself. Coordinates, geology, stratigraphy, wells, reserves, and all other properties still require separate evidence and expert review.

`geological_context` stores provenance including source code, external-record UUID, and upstream external id.

## 6. Protecting reviewer decisions

A link is reviewer-locked if it is `VERIFIED`/`REJECTED`, uses `MANUAL`, has `verified_by`, or has a review comment. Later external sync/process operations cannot silently overwrite it. If an upstream name changes, only unresolved automatic `REVIEW_REQUIRED` links may be recalculated.

## 7. Current v0.2-dev limitation

Full authentication and AuditLog are not implemented yet, so `reviewer` is supplied explicitly in the request body. Before production this will be replaced by authenticated user identity and all review actions will be recorded in audit/revision history.

## 8. Recommended workflow

```text
register → schema → sync → process → review queue
  → confirm / reject / manual link / create DRAFT
  → geological verification
  → only then VERIFIED master data
```

Related documents: `KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`, `EXTERNAL_API_KEYS_EN.md`, `USER_GUIDE_EN.md`, and `PROJECT_PLAN_V0_2_EN.md`.
