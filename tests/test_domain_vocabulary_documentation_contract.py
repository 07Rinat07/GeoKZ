from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

DOMAIN_BINDING_DOCS = (
    DOCS / "DOMAIN_VOCABULARY_BINDINGS_RU.md",
    DOCS / "DOMAIN_VOCABULARY_BINDINGS_KK.md",
    DOCS / "DOMAIN_VOCABULARY_BINDINGS_EN.md",
)


def test_trilingual_domain_vocabulary_binding_docs_follow_safety_contract() -> None:
    for path in DOMAIN_BINDING_DOCS:
        assert path.is_file(), f"Missing domain vocabulary binding guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert "20260905_0007" in content
        assert "DomainVocabularyNormalizer" in content
        assert "lithology_codes" in content
        assert "marker_type_code" in content
        assert "property_kind_code" in content
        assert "unit_code" in content
        assert "flow_rate_unit_code" in content
        assert "RESOLVED" in content
        assert "UNRESOLVED" in content
        assert "AMBIGUOUS" in content
        assert "RAW" in content
        assert "commit()" in content
        assert "atomic" in content.casefold()
