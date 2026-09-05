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

TRILINGUAL_LICENSE_REVIEW_GUIDES = (
    DOCS / "KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md",
    DOCS / "KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md",
    DOCS / "KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md",
)

TRILINGUAL_REVIEW_UI_CONTRACTS = (
    DOCS / "EXTERNAL_REVIEW_UI_CONTRACT_RU.md",
    DOCS / "EXTERNAL_REVIEW_UI_CONTRACT_KK.md",
    DOCS / "EXTERNAL_REVIEW_UI_CONTRACT_EN.md",
)

TRILINGUAL_SYNC_SCHEDULER_GUIDES = (
    DOCS / "EXTERNAL_SYNC_SCHEDULER_RU.md",
    DOCS / "EXTERNAL_SYNC_SCHEDULER_KK.md",
    DOCS / "EXTERNAL_SYNC_SCHEDULER_EN.md",
)

TRILINGUAL_CROSS_SECTION_CONTRACTS = (
    DOCS / "CROSS_SECTION_VIEW_CONTRACT_RU.md",
    DOCS / "CROSS_SECTION_VIEW_CONTRACT_KK.md",
    DOCS / "CROSS_SECTION_VIEW_CONTRACT_EN.md",
)

TRILINGUAL_DEMO_WORKFLOW_GUIDES = (
    DOCS / "DEMO_CORRELATION_WORKFLOW_RU.md",
    DOCS / "DEMO_CORRELATION_WORKFLOW_KK.md",
    DOCS / "DEMO_CORRELATION_WORKFLOW_EN.md",
)

PROCESS_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process"
REVIEW_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review"
REVIEW_VIEW_ENDPOINT = (
    "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view"
)
LICENSE_PROCESS_ENDPOINT = (
    "/api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process"
)
LICENSE_REVIEW_ENDPOINT = (
    "/api/v1/integrations/kazakhstan/"
    "kz-egov-geological-study-licenses/review/records"
)
SYNC_ALL_ENDPOINT = "/api/v1/integrations/sync-all"
SCHEDULER_STATUS_ENDPOINT = "/api/v1/integrations/scheduler/status"
RUN_DUE_ENDPOINT = "/api/v1/integrations/scheduler/run-due"
CROSS_SECTION_ENDPOINT = "/api/v1/correlation/wells/view"
DEMO_WORKFLOW_ENDPOINT = "/api/v1/correlation/demo/workflow"


def test_trilingual_user_guides_exist_and_are_not_empty() -> None:
    for path in TRILINGUAL_USER_GUIDES:
        assert path.is_file(), f"Missing user guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 500
        assert PROCESS_ENDPOINT in content
        assert REVIEW_ENDPOINT in content
        assert REVIEW_VIEW_ENDPOINT in content
        assert SYNC_ALL_ENDPOINT in content
        assert SCHEDULER_STATUS_ENDPOINT in content
        assert CROSS_SECTION_ENDPOINT in content
        assert DEMO_WORKFLOW_ENDPOINT in content
        assert LICENSE_PROCESS_ENDPOINT in content
        assert LICENSE_REVIEW_ENDPOINT in content


def test_trilingual_roadmaps_exist_and_are_not_empty() -> None:
    for path in TRILINGUAL_ROADMAPS:
        assert path.is_file(), f"Missing roadmap: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 1000
        assert PROCESS_ENDPOINT in content
        assert REVIEW_ENDPOINT in content
        assert REVIEW_VIEW_ENDPOINT in content
        assert SYNC_ALL_ENDPOINT in content
        assert RUN_DUE_ENDPOINT in content
        assert CROSS_SECTION_ENDPOINT in content
        assert DEMO_WORKFLOW_ENDPOINT in content
        assert LICENSE_PROCESS_ENDPOINT in content
        assert LICENSE_REVIEW_ENDPOINT in content


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


def test_trilingual_license_review_guides_follow_record_review_contract() -> None:
    for path in TRILINGUAL_LICENSE_REVIEW_GUIDES:
        assert path.is_file(), f"Missing geological license review guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert "zher_koinauyn_geologiyalyk_zer2" in content
        assert "v6" in content
        assert "geological_study_license" in content
        assert LICENSE_PROCESS_ENDPOINT in content
        assert LICENSE_REVIEW_ENDPOINT in content
        assert "REVIEW_REQUIRED" in content
        assert "ACCEPTED" in content
        assert "ExternalEntityLink" in content
        assert "NOT_APPLICABLE" in content
        assert "raw_payload" in content
        assert "reviewed_by" in content
        assert "reviewed_at" in content
        assert "review_comment" in content
        assert "GEOKZ_EGOV_API_KEY" in content
        assert "20260905_0008" in content


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


def test_trilingual_sync_scheduler_guides_exist_and_follow_safety_contract() -> None:
    for path in TRILINGUAL_SYNC_SCHEDULER_GUIDES:
        assert path.is_file(), f"Missing sync scheduler guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert SYNC_ALL_ENDPOINT in content
        assert SCHEDULER_STATUS_ENDPOINT in content
        assert RUN_DUE_ENDPOINT in content
        assert "ALREADY_RUNNING" in content
        assert "SKIPPED_NOT_DUE" in content
        assert "GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS" in content
        assert "GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS" in content
        assert "python -m scripts.external_sync_scheduler" in content
        assert "RUNNING" in content
        assert "FAILED" in content


def test_trilingual_cross_section_contracts_exist_and_follow_depth_safety() -> None:
    for path in TRILINGUAL_CROSS_SECTION_CONTRACTS:
        assert path.is_file(), f"Missing cross-section contract: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert CROSS_SECTION_ENDPOINT in content
        assert "TVDSS" in content
        assert "TVD" in content
        assert "MD" in content
        assert "renderable" in content
        assert "MARKER" in content
        assert "HORIZON" in content
        assert "DEPTH_REFERENCE_MISMATCH" in content
        assert "NO_RENDERABLE_DATA" in content
        assert "NO_CORRELATION_LINES" in content
        assert "VerificationStatus" in content


def test_trilingual_demo_workflow_guides_exist_and_follow_safety_contract() -> None:
    for path in TRILINGUAL_DEMO_WORKFLOW_GUIDES:
        assert path.is_file(), f"Missing demo workflow guide: {path.name}"
        content = path.read_text(encoding="utf-8").strip()
        assert len(content) > 2500
        assert DEMO_WORKFLOW_ENDPOINT in content
        assert "synthetic-correlation-demo-v1" in content
        assert "synthetic=true" in content
        assert "DISCOVERY" in content
        assert "CROSS_SECTION_READY" in content
        assert "reference_well_id" in content
        assert "well_ids" in content
        assert "TVDSS" in content
        assert "production" in content
        assert "422" in content
        assert "python -m scripts.seed_correlation_demo" in content


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
    assert "KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md" in content
    assert "KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md" in content
    assert "KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md" in content
    assert "EXTERNAL_REVIEW_UI_CONTRACT_RU.md" in content
    assert "EXTERNAL_REVIEW_UI_CONTRACT_KK.md" in content
    assert "EXTERNAL_REVIEW_UI_CONTRACT_EN.md" in content
    assert "EXTERNAL_SYNC_SCHEDULER_RU.md" in content
    assert "EXTERNAL_SYNC_SCHEDULER_KK.md" in content
    assert "EXTERNAL_SYNC_SCHEDULER_EN.md" in content
    assert "CROSS_SECTION_VIEW_CONTRACT_RU.md" in content
    assert "CROSS_SECTION_VIEW_CONTRACT_KK.md" in content
    assert "CROSS_SECTION_VIEW_CONTRACT_EN.md" in content
    assert "DEMO_CORRELATION_WORKFLOW_RU.md" in content
    assert "DEMO_CORRELATION_WORKFLOW_KK.md" in content
    assert "DEMO_CORRELATION_WORKFLOW_EN.md" in content
