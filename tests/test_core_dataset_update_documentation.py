from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GUIDES = tuple(
    DOCS / f"CORE_DATASET_UPDATE_CHANNEL_{language}.md"
    for language in ("RU", "KK", "EN")
)

STATUS_ENDPOINT = "/api/v1/core-dataset/update/status"
APPLY_ENDPOINT = "/api/v1/core-dataset/update/apply"
ROLLBACK_ENDPOINT = "/api/v1/core-dataset/update/rollback"


def test_trilingual_core_dataset_update_guides_follow_signed_release_contract() -> None:
    required = (
        STATUS_ENDPOINT,
        APPLY_ENDPOINT,
        ROLLBACK_ENDPOINT,
        "Ed25519",
        "SHA-256",
        "GEOKZ_CORE_DATASET_UPDATE_MANIFEST_URL",
        "GEOKZ_CORE_DATASET_UPDATE_TRUSTED_PUBLIC_KEYS",
        "DISABLED",
        "CURRENT",
        "AVAILABLE",
        "INCOMPATIBLE",
        "FAILED",
        "20260905_0011",
        "AuditLog",
        "admin",
        "external_id",
        "rollback",
    )
    for path in GUIDES:
        assert path.is_file(), f"Missing Core Dataset update guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 3000, f"Core Dataset update guide is too small: {path.name}"
        for value in required:
            assert value in content, f"Missing {value!r} in {path.name}"


def test_documentation_policy_registers_core_dataset_update_guides() -> None:
    policy = (DOCS / "DOCUMENTATION_POLICY.md").read_text(encoding="utf-8")
    for path in GUIDES:
        assert path.name in policy
    assert STATUS_ENDPOINT in policy
    assert APPLY_ENDPOINT in policy
    assert ROLLBACK_ENDPOINT in policy
    assert "Signed updates" in policy
    assert "No destructive rollback" in policy
