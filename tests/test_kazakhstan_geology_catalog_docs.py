from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GUIDES = tuple(DOCS / f"KAZAKHSTAN_GEOLOGY_CATALOG_{lang}.md" for lang in ("RU", "KK", "EN"))


def test_kazakhstan_geology_catalog_guides_are_trilingual_and_safe() -> None:
    required = (
        "stat_kgn_118",
        "stat_kgn_120",
        "LATEST_MAPPING",
        "/api/v4/mapping/{apiUri}",
        "/api/v1/integrations/kazakhstan/{code}/schema",
        "sync_supported=false",
        "processing_supported=false",
        "GEOKZ_EGOV_API_KEY",
        "ExternalEntityLink=VERIFIED",
        "GeologicalEntity=VERIFIED",
        "DRAFT",
        "Sarmuldin Rinat",
        "ura07srr@gmail.com",
    )
    for path in GUIDES:
        assert path.is_file(), f"Missing documentation file: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 3000, f"Documentation file is too small: {path.name}"
        for value in required:
            assert value in content, f"Missing {value!r} in {path.name}"
