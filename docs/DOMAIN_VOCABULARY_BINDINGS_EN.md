# GeoKZ — controlled vocabulary bindings for subsurface models (EN)

Status: `v0.3`, 2026-09-05.

## Purpose

After introducing the persistent controlled vocabulary registry, GeoKZ adds separate canonical-code fields to well, core, well-log, and test models. This is not a destructive migration of source text: existing RAW/source fields remain unchanged while a canonical code is stored beside them as the result of safe normalization.

## New fields

- `WellInterval.lithologies` remains the source list; `WellInterval.lithology_codes` stores canonical `lithology` codes.
- `WellInterval.flow_rate_unit` remains the source unit string; `flow_rate_unit_code` stores a canonical `unit` code.
- `CoreSample.lithologies` is preserved; `CoreSample.lithology_codes` adds canonical codes.
- `WellMarker.marker_type` is preserved; `marker_type_code` references the `marker_type` vocabulary logically.
- `WellLogCurve.property_kind` is preserved; `property_kind_code` uses the `property_kind` vocabulary.
- `WellLogCurve.unit_original` and the existing free-form `canonical_unit` are not removed; `unit_code` stores the stable controlled code.
- `WellTest.oil_rate_unit`, `gas_rate_unit`, and `water_rate_unit` are preserved; `oil_rate_unit_code`, `gas_rate_unit_code`, and `water_rate_unit_code` are added beside them.

Alembic revision: `20260905_0007`. New scalar code columns are nullable, so the migration is backward-compatible with existing records. New `lithology_codes` fields are empty JSONB arrays by default and the schema upgrade does not reinterpret historical data automatically.

## DomainVocabularyNormalizer

`app.application.domain_vocabulary.DomainVocabularyNormalizer` performs deterministic exact resolution through the existing controlled vocabulary service. It deliberately provides no fuzzy/semantic auto-match and it never calls `commit()`; transaction ownership remains with the calling application/import/review workflow.

Supported operations are:

```text
normalize_well_interval
normalize_core_sample
normalize_well_marker
normalize_well_log_curve
normalize_well_test
```

A scalar field is changed only when resolution returns `RESOLVED`. For `UNRESOLVED` or `AMBIGUOUS`, the existing canonical assignment is left untouched and an issue is added to the normalization report.

List fields follow a stricter atomic policy: if any source lithology does not resolve uniquely, the entire `lithology_codes` value remains unchanged. This prevents a partially normalized list from appearing complete and protects previously reviewed assignments.

## Example

Source record:

```text
lithologies = ["Sandstone", "unclassified rock"]
lithology_codes = ["reviewed-existing-code"]
```

If `Sandstone` resolves but the second value is `UNRESOLVED`, the normalizer reports the issue and leaves `lithology_codes` unchanged. The raw lithology list is also untouched.

A well-log curve may therefore contain:

```text
mnemonic_original = GR
property_kind = GR
property_kind_code = gamma_ray
unit_original = API
unit_code = api_deg
```

`mnemonic_original`, `property_kind`, and `unit_original` remain provenance-bearing source data; canonical codes are intended for search, filtering, comparison, and future UI behavior.

## Safety rules

1. Successful resolution never removes the RAW/source value.
2. Only active controlled terms participate in normalization.
3. `UNRESOLVED` and `AMBIGUOUS` never clear an existing canonical assignment.
4. List normalization is atomic; partial success is not published as a complete canonical list.
5. The normalizer does not commit and therefore does not hide the review/transaction boundary.
6. No automatic bulk backfill is run for historical records. Backfill must be a separate reviewable workflow with explicit unresolved/ambiguous reporting.
7. A controlled code does not replace evidence/source provenance and never upgrades geological-object `VerificationStatus` automatically.

## Next roadmap step

Once the controlled-vocabulary P0 is complete, the next planned item is normalization/review for the geological-study license registry after rechecking the official mapping, license/terms, and data quality. A UI may display raw values and canonical codes side by side, but matching business rules must remain backend-owned.
