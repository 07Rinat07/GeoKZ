from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

TRILINGUAL_USER_GUIDES = tuple(DOCS / f"USER_GUIDE_{lang}.md" for lang in ("RU", "KK", "EN"))
TRILINGUAL_ROADMAPS = (
    DOCS / "PROJECT_PLAN_V0_2.md",
    DOCS / "PROJECT_PLAN_V0_2_KK.md",
    DOCS / "PROJECT_PLAN_V0_2_EN.md",
)
TRILINGUAL_CORE_DATASET_GUIDES = tuple(
    DOCS / f"CORE_DATASET_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_API_KEY_GUIDES = tuple(
    DOCS / f"EXTERNAL_API_KEYS_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_KZ_OPEN_DATA_GUIDES = tuple(
    DOCS / f"KAZAKHSTAN_OPEN_DATA_INTEGRATION_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_FIELD_REVIEW_GUIDES = tuple(
    DOCS / f"KAZAKHSTAN_FIELD_REVIEW_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_LICENSE_REVIEW_GUIDES = tuple(
    DOCS / f"KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_{lang}.md"
    for lang in ("RU", "KK", "EN")
)
TRILINGUAL_REVIEW_UI_CONTRACTS = tuple(
    DOCS / f"EXTERNAL_REVIEW_UI_CONTRACT_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_SYNC_SCHEDULER_GUIDES = tuple(
    DOCS / f"EXTERNAL_SYNC_SCHEDULER_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_CROSS_SECTION_CONTRACTS = tuple(
    DOCS / f"CROSS_SECTION_VIEW_CONTRACT_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_DEMO_WORKFLOW_GUIDES = tuple(
    DOCS / f"DEMO_CORRELATION_WORKFLOW_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_AUTH_GUIDES = tuple(
    DOCS / f"AUTH_AUDIT_REVISIONS_{lang}.md" for lang in ("RU", "KK", "EN")
)
TRILINGUAL_DESKTOP_GUIDES = tuple(
    DOCS / f"DESKTOP_CLIENT_{lang}.md" for lang in ("RU", "KK", "EN")
)

PROCESS_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process"
REVIEW_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review"
REVIEW_VIEW_ENDPOINT = "/api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view"
LICENSE_PROCESS_ENDPOINT = (
    "/api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process"
)
LICENSE_REVIEW_ENDPOINT = (
    "/api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records"
)
SYNC_ALL_ENDPOINT = "/api/v1/integrations/sync-all"
SCHEDULER_STATUS_ENDPOINT = "/api/v1/integrations/scheduler/status"
RUN_DUE_ENDPOINT = "/api/v1/integrations/scheduler/run-due"
CROSS_SECTION_ENDPOINT = "/api/v1/correlation/wells/view"
DEMO_WORKFLOW_ENDPOINT = "/api/v1/correlation/demo/workflow"
CORE_DATASET_STATUS_ENDPOINT = "/api/v1/core-dataset/status"
CORE_DATASET_INSTALL_ENDPOINT = "/api/v1/core-dataset/install"
AUTH_LOGIN_ENDPOINT = "/api/v1/auth/login"
AUTH_ME_ENDPOINT = "/api/v1/auth/me"
AUDIT_LOGS_ENDPOINT = "/api/v1/audit/logs"
AUDIT_REVISIONS_ENDPOINT = "/api/v1/audit/revisions/{resource_type}/{resource_id}"
SYSTEM_VERSIONS_ENDPOINT = "/api/v1/system/versions"


def _content(path: Path, *, minimum: int) -> str:
    assert path.is_file(), f"Missing documentation file: {path.name}"
    content = path.read_text(encoding="utf-8").strip()
    assert len(content) > minimum, f"Documentation file is too small: {path.name}"
    return content


def test_trilingual_user_guides_follow_current_product_contract() -> None:
    required = (
        PROCESS_ENDPOINT,
        REVIEW_ENDPOINT,
        REVIEW_VIEW_ENDPOINT,
        SYNC_ALL_ENDPOINT,
        SCHEDULER_STATUS_ENDPOINT,
        CROSS_SECTION_ENDPOINT,
        DEMO_WORKFLOW_ENDPOINT,
        LICENSE_PROCESS_ENDPOINT,
        LICENSE_REVIEW_ENDPOINT,
        CORE_DATASET_STATUS_ENDPOINT,
        CORE_DATASET_INSTALL_ENDPOINT,
        AUTH_LOGIN_ENDPOINT,
        AUTH_ME_ENDPOINT,
        AUDIT_LOGS_ENDPOINT,
        AUDIT_REVISIONS_ENDPOINT,
        SYSTEM_VERSIONS_ENDPOINT,
        "geokz-desktop",
        "ExternalEntityLink=VERIFIED",
        "GeologicalEntity=VERIFIED",
    )
    for path in TRILINGUAL_USER_GUIDES:
        content = _content(path, minimum=2500)
        for value in required:
            assert value in content, f"Missing {value!r} in {path.name}"


def test_trilingual_roadmaps_follow_current_delivery_contract() -> None:
    required = (
        PROCESS_ENDPOINT,
        REVIEW_ENDPOINT,
        REVIEW_VIEW_ENDPOINT,
        SYNC_ALL_ENDPOINT,
        SCHEDULER_STATUS_ENDPOINT,
        RUN_DUE_ENDPOINT,
        CROSS_SECTION_ENDPOINT,
        DEMO_WORKFLOW_ENDPOINT,
        LICENSE_PROCESS_ENDPOINT,
        LICENSE_REVIEW_ENDPOINT,
        CORE_DATASET_STATUS_ENDPOINT,
        CORE_DATASET_INSTALL_ENDPOINT,
        AUTH_LOGIN_ENDPOINT,
        AUDIT_LOGS_ENDPOINT,
        SYSTEM_VERSIONS_ENDPOINT,
        "feature/pyside6-data-review-client-v0.3",
        "Core Dataset update channel",
        "exact-head CI green",
    )
    for path in TRILINGUAL_ROADMAPS:
        content = _content(path, minimum=3000)
        for value in required:
            assert value in content, f"Missing {value!r} in {path.name}"


def test_trilingual_core_dataset_guides_follow_install_safety_contract() -> None:
    for path in TRILINGUAL_CORE_DATASET_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            "2026.09.0-bootstrap",
            "schema_version",
            "SHA-256",
            "geokz-core:",
            CORE_DATASET_STATUS_ENDPOINT,
            CORE_DATASET_INSTALL_ENDPOINT,
            "dry_run",
            "changed=false",
            "manifest.json",
            "CoreDatasetState",
            "minimum_app_version",
            "python -m scripts.core_dataset validate",
        ):
            assert value in content


def test_trilingual_api_key_guides_exist_and_are_not_empty() -> None:
    for path in TRILINGUAL_API_KEY_GUIDES:
        content = _content(path, minimum=1500)
        assert "GEOKZ_EGOV_API_KEY" in content
        assert "data.egov.kz" in content


def test_trilingual_kazakhstan_open_data_guides_follow_contract() -> None:
    for path in TRILINGUAL_KZ_OPEN_DATA_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            "apiUri",
            "record_type",
            "/api/v4/mapping/{apiUri}/{version}",
            "/api/v1/integrations/kazakhstan/{code}/schema",
            PROCESS_ENDPOINT,
            "REVIEW_REQUIRED",
        ):
            assert value in content


def test_trilingual_field_review_guides_follow_safety_contract() -> None:
    for path in TRILINGUAL_FIELD_REVIEW_GUIDES:
        content = _content(path, minimum=2000)
        for value in (
            REVIEW_ENDPOINT,
            "REVIEW_REQUIRED",
            "DRAFT",
            "VERIFIED",
            "manual-link",
            "create-draft-field",
        ):
            assert value in content


def test_trilingual_license_review_guides_follow_record_review_contract() -> None:
    for path in TRILINGUAL_LICENSE_REVIEW_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            "zher_koinauyn_geologiyalyk_zer2",
            "v6",
            "geological_study_license",
            LICENSE_PROCESS_ENDPOINT,
            LICENSE_REVIEW_ENDPOINT,
            "REVIEW_REQUIRED",
            "ACCEPTED",
            "ExternalEntityLink",
            "NOT_APPLICABLE",
            "raw_payload",
            "reviewed_by",
            "reviewed_at",
            "review_comment",
            "GEOKZ_EGOV_API_KEY",
            "20260905_0008",
        ):
            assert value in content


def test_trilingual_review_ui_contracts_follow_action_contract() -> None:
    for path in TRILINGUAL_REVIEW_UI_CONTRACTS:
        content = _content(path, minimum=2500)
        for value in (
            REVIEW_VIEW_ENDPOINT,
            "CONFIRM_LINK",
            "REJECT_LINK",
            "MANUAL_LINK",
            "CREATE_DRAFT_FIELD",
            "required_fields",
            "optional_fields",
            "enabled",
            "DRAFT",
            "VERIFIED",
        ):
            assert value in content


def test_trilingual_sync_scheduler_guides_follow_safety_contract() -> None:
    for path in TRILINGUAL_SYNC_SCHEDULER_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            SYNC_ALL_ENDPOINT,
            SCHEDULER_STATUS_ENDPOINT,
            RUN_DUE_ENDPOINT,
            "ALREADY_RUNNING",
            "SKIPPED_NOT_DUE",
            "GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS",
            "GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS",
            "python -m scripts.external_sync_scheduler",
            "RUNNING",
            "FAILED",
        ):
            assert value in content


def test_trilingual_cross_section_contracts_follow_depth_safety() -> None:
    for path in TRILINGUAL_CROSS_SECTION_CONTRACTS:
        content = _content(path, minimum=2500)
        for value in (
            CROSS_SECTION_ENDPOINT,
            "TVDSS",
            "TVD",
            "MD",
            "renderable",
            "MARKER",
            "HORIZON",
            "DEPTH_REFERENCE_MISMATCH",
            "NO_RENDERABLE_DATA",
            "NO_CORRELATION_LINES",
            "VerificationStatus",
        ):
            assert value in content


def test_trilingual_demo_workflow_guides_follow_safety_contract() -> None:
    for path in TRILINGUAL_DEMO_WORKFLOW_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            DEMO_WORKFLOW_ENDPOINT,
            "synthetic-correlation-demo-v1",
            "synthetic=true",
            "DISCOVERY",
            "CROSS_SECTION_READY",
            "reference_well_id",
            "well_ids",
            "TVDSS",
            "production",
            "422",
            "python -m scripts.seed_correlation_demo",
        ):
            assert value in content


def test_trilingual_auth_guides_follow_identity_and_audit_contract() -> None:
    for path in TRILINGUAL_AUTH_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            AUTH_LOGIN_ENDPOINT,
            AUTH_ME_ENDPOINT,
            "/api/v1/auth/logout",
            AUDIT_LOGS_ENDPOINT,
            "editor",
            "expert",
            "admin",
            "DRAFT",
            "AuditLog",
            "master_data_revisions",
            "authenticated",
        ):
            assert value in content


def test_trilingual_desktop_guides_follow_http_boundary_contract() -> None:
    for path in TRILINGUAL_DESKTOP_GUIDES:
        content = _content(path, minimum=2500)
        for value in (
            "PySide6",
            "GeoKZApiClient",
            "httpx",
            "geokz-desktop",
            AUTH_LOGIN_ENDPOINT,
            SYSTEM_VERSIONS_ENDPOINT,
            SYNC_ALL_ENDPOINT,
            REVIEW_VIEW_ENDPOINT,
            LICENSE_REVIEW_ENDPOINT,
            AUDIT_LOGS_ENDPOINT,
            AUDIT_REVISIONS_ENDPOINT,
            "QThreadPool/QRunnable",
            "ExternalEntityLink=VERIFIED",
            "GeologicalEntity=VERIFIED",
        ):
            assert value in content, f"Missing {value!r} in {path.name}"


def test_documentation_policy_lists_all_trilingual_feature_contracts() -> None:
    content = _content(DOCS / "DOCUMENTATION_POLICY.md", minimum=2500)
    required_names = [
        *(path.name for path in TRILINGUAL_USER_GUIDES),
        *(path.name for path in TRILINGUAL_ROADMAPS),
        *(path.name for path in TRILINGUAL_CORE_DATASET_GUIDES),
        *(path.name for path in TRILINGUAL_API_KEY_GUIDES),
        *(path.name for path in TRILINGUAL_KZ_OPEN_DATA_GUIDES),
        *(path.name for path in TRILINGUAL_FIELD_REVIEW_GUIDES),
        *(path.name for path in TRILINGUAL_LICENSE_REVIEW_GUIDES),
        *(path.name for path in TRILINGUAL_REVIEW_UI_CONTRACTS),
        *(path.name for path in TRILINGUAL_SYNC_SCHEDULER_GUIDES),
        *(path.name for path in TRILINGUAL_CROSS_SECTION_CONTRACTS),
        *(path.name for path in TRILINGUAL_DEMO_WORKFLOW_GUIDES),
        *(path.name for path in TRILINGUAL_AUTH_GUIDES),
        *(path.name for path in TRILINGUAL_DESKTOP_GUIDES),
    ]
    for name in required_names:
        assert name in content, f"Documentation policy does not mention {name}"
    assert "Desktop HTTP boundary" in content
    assert "Append-only history" in content
