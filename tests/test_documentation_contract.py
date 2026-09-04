from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

TRILINGUAL_USER_GUIDES = (
    DOCS / "USER_GUIDE_RU.md",
    DOCS / "USER_GUIDE_KK.md",
    DOCS / "USER_GUIDE_EN.md",
)

TRILINGUAL_ROADMAPS = (
    DOCS / "PROJECT_PLAN_V0_2.md",
    DOCS / "PROJECT_PLAN_V0_2_KK.md",
    DOCS / "PROJECT_PLAN_V0_2_EN.md",
)

TRILINGUAL_API_KEY_GUIDES = (
    DOCS / "EXTERNAL_API_KEYS_RU.md",
    DOCS / "EXTERNAL_API_KEYS_KK.md",
    DOCS / "EXTERNAL_API_KEYS_EN.md",
)

TRILINGUAL_KZ_OPEN_DATA_GUIDES = (
    DOCS / "KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md",
    DOCS / "KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md",
    DOCS / "KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md",
)

TRILINGUAL_FIELD_REVIEW_GUIDES = (
    DOCS / "KAZAKHSTAN_FIELD_REVIEW_RU.md",
    DOCS / "KAZAKHSTAN_FIELD_REVIEW_KK.md",
    DOCS / "KAZAKHSTAN_FIELD_REVIEW_EN.md",
)

TRILINGUAL_REVIEW_UI_CONTRACTS = (
    DOCS / "EXTERNAL_REVIEW_UI_CONTRACT_RU.md",
    DOCS / "EXTERNAL_REVIEW_UI_CONTRACT_KK.md",
    DOCS / "EXTERNAL_REVIEW_UI_CONTRACT_EN.md",
)

PROCESS_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process"
REVIEW_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review"
REVIEW_VIEW_ENDPOINT = (
    "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view"
)


def test_trilingual_user_guides_exist_and_are_not_empty() -> None:
    for path in TRILINGUAL_USER_GUIDES:
        assert path.is_file(), f"Missing user guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 500
        assert PROCESS_ENDPOINT in content
        assert REVIEW_ENDPOINT in content
        assert REVIEW_VIEW_ENDPOINT in content


def test_trilingual_roadmaps_exist_and_are_not_empty() -> None:
    for path in TRILINGUAL_ROADMAPS:
        assert path.is_file(), f"Missing roadmap: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 1000
        assert PROCESS_ENDPOINT in content
        assert REVIEW_ENDPOINT in content
        assert REVIEW_VIEW_ENDPOINT in content


def test_trilingual_api_key_guides_exist_and_are_not_empty() -> None:
    for path in TRILINGUAL_API_KEY_GUIDES:
        assert path.is_file(), f"Missing API key guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 1500
        assert "GEOKZ_EGOV_API_KEY" in content
        assert "data.egov.kz" in content


def test_trilingual_kazakhstan_open_data_guides_exist_and_follow_contract() -> None:
    for path in TRILINGUAL_KZ_OPEN_DATA_GUIDES:
        assert path.is_file(), f"Missing Kazakhstan Open Data guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert "apiUri" in content
        assert "record_type" in content
        assert "/api/v4/mapping/{apiUri}/{version}" in content
        assert "/api/v1/integrations/kazakhstan/{code}/schema" in content
        assert PROCESS_ENDPOINT in content
        assert "REVIEW_REQUIRED" in content


def test_trilingual_field_review_guides_exist_and_follow_safety_contract() -> None:
    for path in TRILINGUAL_FIELD_REVIEW_GUIDES:
        assert path.is_file(), f"Missing field review guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2000
        assert REVIEW_ENDPOINT in content
        assert "REVIEW_REQUIRED" in content
        assert "DRAFT" in content
        assert "VERIFIED" in content
        assert "manual-link" in content
        assert "create-draft-field" in content


def test_trilingual_review_ui_contracts_exist_and_follow_action_contract() -> None:
    for path in TRILINGUAL_REVIEW_UI_CONTRACTS:
        assert path.is_file(), f"Missing review UI contract: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert REVIEW_VIEW_ENDPOINT in content
        assert "CONFIRM_LINK" in content
        assert "REJECT_LINK" in content
        assert "MANUAL_LINK" in content
        assert "CREATE_DRAFT_FIELD" in content
        assert "required_fields" in content
        assert "optional_fields" in content
        assert "enabled" in content
        assert "DRAFT" in content
        assert "VERIFIED" in content


def test_documentation_policy_exists() -> None:
    policy = DOCS / "DOCUMENTATION_POLICY.md"
    assert policy.is_file()
    content = policy.read_text(encoding="utf-8")
    assert "USER_GUIDE_RU.md" in content
    assert "USER_GUIDE_KK.md" in content
    assert "USER_GUIDE_EN.md" in content
    assert "PROJECT_PLAN_V0_2_KK.md" in content
    assert "PROJECT_PLAN_V0_2_EN.md" in content
    assert "EXTERNAL_API_KEYS_RU.md" in content
    assert "EXTERNAL_API_KEYS_KK.md" in content
    assert "EXTERNAL_API_KEYS_EN.md" in content
    assert "KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md" in content
    assert "KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md" in content
    assert "KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md" in content
    assert "KAZAKHSTAN_FIELD_REVIEW_RU.md" in content
    assert "KAZAKHSTAN_FIELD_REVIEW_KK.md" in content
    assert "KAZAKHSTAN_FIELD_REVIEW_EN.md" in content
    assert "EXTERNAL_REVIEW_UI_CONTRACT_RU.md" in content
    assert "EXTERNAL_REVIEW_UI_CONTRACT_KK.md" in content
    assert "EXTERNAL_REVIEW_UI_CONTRACT_EN.md" in content
