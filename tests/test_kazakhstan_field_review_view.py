from uuid import uuid4

from app.application.kazakhstan_field_review import FieldReviewLink, FieldReviewRecord
from app.application.kazakhstan_field_review_view import build_field_review_queue_view
from app.integrations.types import (
    EntityLinkStatus,
    ExternalRecordStatus,
    FieldReviewActionCode,
    FieldReviewMatchStatus,
    MatchMethod,
)
from app.models.enums import VerificationStatus
from app.schemas.integration import FieldReviewQueueViewRead


def test_unmatched_review_view_exposes_manual_and_draft_actions() -> None:
    record_id = uuid4()
    record = FieldReviewRecord(
        record_id=record_id,
        external_id="upstream-unmatched-1",
        raw_payload={"name": "TEST UNMATCHED"},
        normalized_payload={
            "name_ru": "TEST UNMATCHED",
            "matching": {"status": "UNMATCHED"},
        },
        status=ExternalRecordStatus.REVIEW_REQUIRED,
        links=(),
    )

    view = build_field_review_queue_view(
        records=[record],
        total_pending=2,
        language="kk",
        limit=1,
        offset=0,
    )
    response = FieldReviewQueueViewRead.model_validate(view)

    assert response.language == "kk"
    assert response.total_pending == 2
    assert response.returned_count == 1
    assert response.has_more is True
    assert response.records[0].matching_status == FieldReviewMatchStatus.UNMATCHED
    assert response.records[0].display_name == "TEST UNMATCHED"

    actions = {action.code: action for action in response.records[0].actions}
    manual = actions[FieldReviewActionCode.MANUAL_LINK]
    create_draft = actions[FieldReviewActionCode.CREATE_DRAFT_FIELD]
    assert manual.enabled is True
    assert manual.required_fields == ["entity_id", "reviewer"]
    assert manual.path.endswith(f"/review/{record_id}/manual-link")
    assert create_draft.enabled is True
    assert create_draft.disabled_reason is None
    assert create_draft.path.endswith(f"/review/{record_id}/create-draft-field")


def test_rejected_candidate_is_localized_and_not_actionable() -> None:
    record_id = uuid4()
    link_id = uuid4()
    entity_id = uuid4()
    link = FieldReviewLink(
        link_id=link_id,
        entity_id=entity_id,
        entity_name_ru="ТЕСТОВОЕ МЕСТОРОЖДЕНИЕ",
        entity_name_kk="ТЕСТ КЕН ОРНЫ",
        entity_name_en="TEST FIELD",
        entity_verification_status=VerificationStatus.VERIFIED,
        match_method=MatchMethod.ALIAS,
        match_confidence=0.91,
        status=EntityLinkStatus.REJECTED,
        verified_by="Reviewer",
        review_comment="Rejected earlier",
    )
    record = FieldReviewRecord(
        record_id=record_id,
        external_id="upstream-ambiguous-1",
        raw_payload={"name": "TEST FIELD"},
        normalized_payload={
            "name_ru": "TEST FIELD",
            "matching": {"status": "AMBIGUOUS"},
        },
        status=ExternalRecordStatus.REVIEW_REQUIRED,
        links=(link,),
    )

    view = build_field_review_queue_view(
        records=[record],
        total_pending=1,
        language="en",
        limit=100,
        offset=0,
    )
    response = FieldReviewQueueViewRead.model_validate(view)
    candidate = response.records[0].candidates[0]

    assert candidate.entity_display_name == "TEST FIELD"
    assert candidate.entity_verification_status == VerificationStatus.VERIFIED
    assert candidate.status == EntityLinkStatus.REJECTED
    assert all(action.enabled is False for action in candidate.actions)
    assert all(action.disabled_reason for action in candidate.actions)

    record_actions = {action.code: action for action in response.records[0].actions}
    assert record_actions[FieldReviewActionCode.MANUAL_LINK].enabled is True
    assert record_actions[FieldReviewActionCode.CREATE_DRAFT_FIELD].enabled is False
    assert record_actions[FieldReviewActionCode.CREATE_DRAFT_FIELD].disabled_reason


def test_unknown_matching_status_is_safe_for_clients() -> None:
    record = FieldReviewRecord(
        record_id=uuid4(),
        external_id="upstream-future-status",
        raw_payload={},
        normalized_payload={"matching": {"status": "FUTURE_STATUS"}},
        status=ExternalRecordStatus.REVIEW_REQUIRED,
        links=(),
    )

    view = build_field_review_queue_view(
        records=[record],
        total_pending=1,
        language="ru",
        limit=100,
        offset=0,
    )

    assert view.records[0].matching_status == FieldReviewMatchStatus.UNKNOWN
    create_draft = next(
        action
        for action in view.records[0].actions
        if action.code == FieldReviewActionCode.CREATE_DRAFT_FIELD
    )
    assert create_draft.enabled is False
