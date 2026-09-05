# GeoKZ — controlled geological vocabularies (EN)

Status: foundation `v0.3`, 2026-09-05.

## Purpose

GeoKZ provides a persistent controlled-term registry for four categories: `lithology`, `marker_type`, `property_kind`, and `unit`. The registry gives the API, importers, future PySide6 clients, and external connectors stable canonical codes without rewriting the wording of the primary source.

The primary rule is: **RAW/source wording remains preserved and is not replaced by the vocabulary**. A LAS mnemonic, an author's lithology description, or an upstream unit string stays in its original field/RAW payload. A controlled term is an additional normalization layer rather than a replacement for evidence.

## Data model

The `controlled_vocabulary_terms` table stores:

- `vocabulary` — one of the four stable categories;
- `code` — the canonical GeoKZ code within the category;
- `name_ru`, `name_kk`, `name_en` — required localized display names;
- `aliases` — accepted exact variants for deterministic resolution;
- `description` — optional explanatory text;
- `source_reference` — provenance/basis for the term;
- `metadata` — extensible technical attributes such as `symbol`, `quantity_kind`, or typical mnemonics;
- `is_active` — whether the term participates in new normalization.

The pair `(vocabulary, code)` is unique. Geological terminology is not frozen into one large Python Enum; a persistent registry allows the subject dictionary to evolve without changing application code for every new term.

## API

Vocabulary catalog:

```text
GET /api/v1/vocabularies?lang=en
```

Terms for one vocabulary:

```text
GET /api/v1/vocabularies/lithology/terms?lang=en
GET /api/v1/vocabularies/unit/terms?lang=en&include_inactive=false
```

Safe batch resolution of source values:

```text
POST /api/v1/vocabularies/property_kind/resolve?lang=en
```

Example request:

```json
{
  "values": ["GR", "Gamma ray", "unknown parameter"]
}
```

Each input returns `RESOLVED`, `UNRESOLVED`, or `AMBIGUOUS`. There is deliberately no fuzzy auto-matching at this stage. GeoKZ applies case-insensitive exact matching after whitespace normalization against `code`, the three localized names, and aliases. If an alias maps to more than one term, the service returns `AMBIGUOUS` instead of making an arbitrary choice.

## Bootstrap dataset

The initial dictionary is stored at:

```text
data/bootstrap/controlled_vocabularies.json
```

It is an **initial internal dictionary**, not a claim of complete or authoritative Kazakhstan geological classification. It provides a minimum starting set for lithologies, marker types, well-log/property kinds, and units. Production extensions require subject-matter review and a non-empty `source_reference`.

Idempotent loading is provided by:

```text
python -m scripts.seed_controlled_vocabularies
```

The script upserts by `(vocabulary, code)`. Schema migration and dataset seeding are intentionally separate: Alembic creates the table structure while the bootstrap dataset is loaded independently.

## Safety and provenance rules

1. A controlled term never deletes the original value from a document, LAS/DLIS/WITSML file, external API payload, or expert input.
2. `source_reference` is mandatory, including for bootstrap terms.
3. Inactive terms do not participate in the default resolver.
4. Future fuzzy/semantic matching may create review candidates only; it must not silently assign a canonical code.
5. Public write/edit endpoints are deliberately absent for now. Administrative vocabulary mutation should be added only after Authentication + AuditLog/revisions so terminology changes have an attributable author and history.
6. Units use canonical codes with `symbol` and `quantity_kind` metadata. Numeric conversion must never be inferred only from a similar-looking unit string without an explicit conversion rule.

## Next step

After this foundation, canonical codes will be attached to domain models **without removing raw fields**: `WellInterval/CoreSample` for lithology, `WellMarker` for marker type, `WellLogCurve` for property kind/unit, and rate-unit fields for tests/intervals. The migration must remain backward-compatible and normalization must explicitly distinguish raw value, resolved canonical code, and unresolved/review-required state.
