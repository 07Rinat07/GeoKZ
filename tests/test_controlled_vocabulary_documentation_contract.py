from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CONTROLLED_VOCABULARY_DOCS = (
    DOCS / "CONTROLLED_VOCABULARIES_RU.md",
    DOCS / "CONTROLLED_VOCABULARIES_KK.md",
    DOCS / "CONTROLLED_VOCABULARIES_EN.md",
)

CATALOG_ENDPOINT = "/api/v1/vocabularies"
TERMS_ENDPOINT = "/api/v1/vocabularies/lithology/terms"
RESOLVE_ENDPOINT = "/api/v1/vocabularies/property_kind/resolve"


def test_trilingual_controlled_vocabulary_docs_follow_safety_contract() -> None:
    for path in CONTROLLED_VOCABULARY_DOCS:
        assert path.is_file(), f"Missing controlled vocabulary guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert CATALOG_ENDPOINT in content
        assert TERMS_ENDPOINT in content
        assert RESOLVE_ENDPOINT in content
        assert "controlled_vocabulary_terms" in content
        assert "lithology" in content
        assert "marker_type" in content
        assert "property_kind" in content
        assert "unit" in content
        assert "RESOLVED" in content
        assert "UNRESOLVED" in content
        assert "AMBIGUOUS" in content
        assert "source_reference" in content
        assert "python -m scripts.seed_controlled_vocabularies" in content
        assert "RAW" in content
        assert "fuzzy" in content.casefold()
