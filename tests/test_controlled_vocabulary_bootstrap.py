import json
from pathlib import Path

from app.models.enums import VocabularyCode

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "data" / "bootstrap" / "controlled_vocabularies.json"


def test_controlled_vocabulary_bootstrap_has_required_contract() -> None:
    payload = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    assert payload["version"] == "1.0.0"
    assert payload["status"] == "initial_internal_dictionary"

    terms = payload["terms"]
    assert terms
    vocabularies = {term["vocabulary"] for term in terms}
    assert vocabularies == {item.value for item in VocabularyCode}

    seen: set[tuple[str, str]] = set()
    for term in terms:
        key = (term["vocabulary"], term["code"])
        assert key not in seen
        seen.add(key)

        assert term["code"].strip()
        assert term["name_ru"].strip()
        assert term["name_kk"].strip()
        assert term["name_en"].strip()
        assert term["source_reference"].strip()
        assert isinstance(term.get("aliases", []), list)
        assert isinstance(term.get("metadata", {}), dict)

        if term["vocabulary"] == VocabularyCode.UNIT.value:
            metadata = term["metadata"]
            assert metadata["symbol"]
            assert metadata["quantity_kind"]


def test_bootstrap_policy_preserves_raw_source_wording() -> None:
    payload = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    policy = payload["policy"].casefold()
    assert "raw/source wording remains preserved" in policy
    assert "expert review" in policy
