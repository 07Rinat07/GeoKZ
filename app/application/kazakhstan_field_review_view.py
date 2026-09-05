from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.kazakhstan_field_processing import OIL_GAS_FIELDS_SOURCE_CODE
from app.application.kazakhstan_field_review import (
    FieldReviewLink,
    FieldReviewRecord,
    KazakhstanOilGasFieldReviewService,
)
from app.core.project_info import SupportedLanguage
from app.integrations.types import (
    EntityLinkStatus,
    ExternalRecordStatus,
    FieldReviewActionCode,
    FieldReviewMatchStatus,
    MatchMethod,
)
from app.models.enums import VerificationStatus


@dataclass(frozen=True, slots=True)
class FieldReviewActionView:
    code: FieldReviewActionCode
    label: str
    method: str
    path: str
    enabled: bool
    disabled_reason: str | None
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FieldReviewCandidateView:
    link_id: UUID
    entity_id: UUID
    entity_display_name: str
    entity_verification_status: VerificationStatus
    match_method: MatchMethod
    match_confidence: float
    status: EntityLinkStatus
    verified_by: str | None
    review_comment: str | None
    actions: tuple[FieldReviewActionView, ...]


@dataclass(frozen=True, slots=True)
class FieldReviewRecordView:
    record_id: UUID
    external_id: str
    display_name: str
    status: ExternalRecordStatus
    matching_status: FieldReviewMatchStatus
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None
    candidates: tuple[FieldReviewCandidateView, ...]
    actions: tuple[FieldReviewActionView, ...]


@dataclass(frozen=True, slots=True)
class FieldReviewQueueView:
    source_code: str
    language: SupportedLanguage
    title: str
    policy_note: str
    total_pending: int
    returned_count: int
    limit: int
    offset: int
    has_more: bool
    records: tuple[FieldReviewRecordView, ...]


_TEXT = {
    "ru": {
        "title": "Проверка внешних нефтегазовых месторождений",
        "policy_note": (
            "Подтверждение связи с официальной записью не делает геологический объект VERIFIED; "
            "геологические свойства и интерпретации подтверждаются отдельно. "
            "Личность эксперта берётся из авторизованной сессии."
        ),
        "confirm": "Подтвердить связь",
        "reject": "Отклонить связь",
        "manual": "Связать вручную",
        "create_draft": "Создать DRAFT месторождение",
        "locked_link": "Решение по этой связи уже зафиксировано экспертом.",
        "draft_only_unmatched": "Создание нового объекта доступно только для UNMATCHED записи.",
    },
    "kk": {
        "title": "Сыртқы мұнай-газ кен орындарын сараптамалық тексеру",
        "policy_note": (
            "Ресми жазбамен расталған байланыс геологиялық объектіні VERIFIED етпейді; "
            "геологиялық қасиеттер мен интерпретациялар бөлек тексеріледі. "
            "Сарапшының тұлғасы авторизацияланған сессиядан алынады."
        ),
        "confirm": "Байланысты растау",
        "reject": "Байланысты қабылдамау",
        "manual": "Қолмен байланыстыру",
        "create_draft": "DRAFT кен орнын жасау",
        "locked_link": "Бұл байланыс бойынша сарапшы шешімі бұрыннан бекітілген.",
        "draft_only_unmatched": "Жаңа объект тек UNMATCHED жазбасы үшін жасалады.",
    },
    "en": {
        "title": "Expert review of external oil and gas fields",
        "policy_note": (
            "Verifying a link to an official record does not make the geological entity VERIFIED; "
            "geological properties and interpretations require separate evidence and review. "
            "Reviewer identity is derived from the authenticated session."
        ),
        "confirm": "Confirm link",
        "reject": "Reject link",
        "manual": "Link manually",
        "create_draft": "Create DRAFT field",
        "locked_link": "An expert decision for this link is already locked.",
        "draft_only_unmatched": "A new entity can be created only for an UNMATCHED record.",
    },
}


def _matching_status(record: FieldReviewRecord) -> FieldReviewMatchStatus:
    matching = (record.normalized_payload or {}).get("matching")
    value = matching.get("status") if isinstance(matching, dict) else None
    if not isinstance(value, str):
        return FieldReviewMatchStatus.UNKNOWN
    try:
        return FieldReviewMatchStatus(value)
    except ValueError:
        return FieldReviewMatchStatus.UNKNOWN


def _record_display_name(record: FieldReviewRecord) -> str:
    payload = record.normalized_payload or {}
    for key in ("name_ru", "name_kk", "name_en"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return record.external_id


def _localized_entity_name(
    link: FieldReviewLink,
    language: SupportedLanguage,
) -> str:
    names = {
        "ru": (link.entity_name_ru, link.entity_name_kk, link.entity_name_en),
        "kk": (link.entity_name_kk, link.entity_name_ru, link.entity_name_en),
        "en": (link.entity_name_en, link.entity_name_ru, link.entity_name_kk),
    }[language]
    return next((name for name in names if name and name.strip()), str(link.entity_id))


def _candidate_actions(
    *,
    record_id: UUID,
    link: FieldReviewLink,
    language: SupportedLanguage,
) -> tuple[FieldReviewActionView, ...]:
    text = _TEXT[language]
    unresolved = link.status in (
        EntityLinkStatus.REVIEW_REQUIRED,
        EntityLinkStatus.AUTO_MATCHED,
    )
    base = (
        f"/api/v1/integrations/kazakhstan/{OIL_GAS_FIELDS_SOURCE_CODE}"
        f"/review/{record_id}/links/{link.link_id}"
    )
    disabled_reason = None if unresolved else text["locked_link"]
    return (
        FieldReviewActionView(
            code=FieldReviewActionCode.CONFIRM_LINK,
            label=text["confirm"],
            method="POST",
            path=f"{base}/confirm",
            enabled=unresolved,
            disabled_reason=disabled_reason,
            required_fields=(),
            optional_fields=("comment",),
        ),
        FieldReviewActionView(
            code=FieldReviewActionCode.REJECT_LINK,
            label=text["reject"],
            method="POST",
            path=f"{base}/reject",
            enabled=unresolved,
            disabled_reason=disabled_reason,
            required_fields=("comment",),
            optional_fields=(),
        ),
    )


def _record_actions(
    *,
    record: FieldReviewRecord,
    matching_status: FieldReviewMatchStatus,
    language: SupportedLanguage,
) -> tuple[FieldReviewActionView, ...]:
    text = _TEXT[language]
    base = (
        f"/api/v1/integrations/kazakhstan/{OIL_GAS_FIELDS_SOURCE_CODE}"
        f"/review/{record.record_id}"
    )
    can_create_draft = matching_status == FieldReviewMatchStatus.UNMATCHED
    return (
        FieldReviewActionView(
            code=FieldReviewActionCode.MANUAL_LINK,
            label=text["manual"],
            method="POST",
            path=f"{base}/manual-link",
            enabled=True,
            disabled_reason=None,
            required_fields=("entity_id",),
            optional_fields=("comment",),
        ),
        FieldReviewActionView(
            code=FieldReviewActionCode.CREATE_DRAFT_FIELD,
            label=text["create_draft"],
            method="POST",
            path=f"{base}/create-draft-field",
            enabled=can_create_draft,
            disabled_reason=(
                None if can_create_draft else text["draft_only_unmatched"]
            ),
            required_fields=(),
            optional_fields=("comment", "name_ru", "name_kk", "name_en"),
        ),
    )


def build_field_review_queue_view(
    *,
    records: list[FieldReviewRecord],
    total_pending: int,
    language: SupportedLanguage,
    limit: int,
    offset: int,
) -> FieldReviewQueueView:
    text = _TEXT[language]
    record_views: list[FieldReviewRecordView] = []

    for record in records:
        matching_status = _matching_status(record)
        candidates = tuple(
            FieldReviewCandidateView(
                link_id=link.link_id,
                entity_id=link.entity_id,
                entity_display_name=_localized_entity_name(link, language),
                entity_verification_status=link.entity_verification_status,
                match_method=link.match_method,
                match_confidence=link.match_confidence,
                status=link.status,
                verified_by=link.verified_by,
                review_comment=link.review_comment,
                actions=_candidate_actions(
                    record_id=record.record_id,
                    link=link,
                    language=language,
                ),
            )
            for link in sorted(
                record.links,
                key=lambda item: (-item.match_confidence, str(item.entity_id)),
            )
        )
        record_views.append(
            FieldReviewRecordView(
                record_id=record.record_id,
                external_id=record.external_id,
                display_name=_record_display_name(record),
                status=record.status,
                matching_status=matching_status,
                raw_payload=record.raw_payload,
                normalized_payload=record.normalized_payload,
                candidates=candidates,
                actions=_record_actions(
                    record=record,
                    matching_status=matching_status,
                    language=language,
                ),
            )
        )

    returned_count = len(record_views)
    return FieldReviewQueueView(
        source_code=OIL_GAS_FIELDS_SOURCE_CODE,
        language=language,
        title=text["title"],
        policy_note=text["policy_note"],
        total_pending=total_pending,
        returned_count=returned_count,
        limit=limit,
        offset=offset,
        has_more=offset + returned_count < total_pending,
        records=tuple(record_views),
    )


@dataclass(slots=True)
class KazakhstanOilGasFieldReviewViewService:
    session: AsyncSession

    async def get_queue(
        self,
        *,
        language: SupportedLanguage,
        limit: int = 100,
        offset: int = 0,
    ) -> FieldReviewQueueView:
        review_service = KazakhstanOilGasFieldReviewService(self.session)
        records = await review_service.list_pending(limit=limit, offset=offset)
        total_pending = await review_service.count_pending()
        return build_field_review_queue_view(
            records=records,
            total_pending=total_pending,
            language=language,
            limit=limit,
            offset=offset,
        )
