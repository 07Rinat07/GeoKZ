from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

GUIDES = (
    DOCS / "LOCAL_CRS_REGISTRY_RU.md",
    DOCS / "LOCAL_CRS_REGISTRY_KK.md",
    DOCS / "LOCAL_CRS_REGISTRY_EN.md",
)

ENDPOINT = "/api/v1/spatial/crs-definitions"


def test_local_crs_guides_exist_and_document_safety_contract() -> None:
    for path in GUIDES:
        assert path.is_file(), f"Missing local CRS guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert ENDPOINT in content
        assert "registered_crs_code" in content
        assert "EPSG" in content
        assert "WKT" in content
        assert "PROJ" in content
        assert "source_reference" in content
        assert "is_confirmed" in content
        assert "selectable_only" in content
        assert "axis_order" in content
        assert "409" in content
        assert "20260904_0005" in content
