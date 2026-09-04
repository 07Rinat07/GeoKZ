from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.kazakhstan_field_processing import OIL_GAS_FIELDS_SOURCE_CODE
from app.application.kazakhstan_field_review import (
    FieldReviewActionResult,
    FieldReviewNotFoundError,
    FieldReviewValidationError,
    KazakhstanOilGasFieldReviewService,
)
from app.application.kazakhstan_field_review_view import (
    KazakhstanOilGasFieldReviewViewService,
)
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.schemas.integration import (
    FieldReviewActionResponse,
    FieldReviewCreateDraftRequest,
    FieldReviewDecisionRequest,
    FieldReviewLinkRead,
    FieldReviewManualLinkRequest,
    FieldReviewQueueViewRead,
    FieldReviewRecordRead,
    FieldReviewRejectRequest,
)

router = APIRouter()


def _ensure_supported_code(code: str) -> None:
    if code != OIL_GAS_FIELDS_SOURCE_CODE:
        raise HTTPException(
            status_code=422,
            detail="Review workflow пока реализован только для нефтегазовых месторождений",
        )


def _action_response(result: FieldReviewActionResult) -> FieldReviewActionResponse:
    return FieldReviewActionResponse(
        record_id=result.record_id,
        record_status=result.record_status,
        link_id=result.link_id,
        link_status=result.link_status,
        entity_id=result.entity_id,
        entity_verification_status=result.entity_verification_status,
    )


def _raise_review_error(error: Exception) -> None:
    if isinstance(error, FieldReviewNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, FieldReviewValidationError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    raise error


@router.get(
    "/kazakhstan/{code}/review/view",
    response_model=FieldReviewQueueViewRead,
)
async def get_field_review_queue_view(
    code: str,
    lang: SupportedLanguage = Query(default="ru"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> FieldReviewQueueViewRead:
    _ensure_supported_code(code)
    try:
        view = await KazakhstanOilGasFieldReviewViewService(session).get_queue(
            language=lang,
            limit=limit,
            offset=offset,
        )
    except Exception as error:
        _raise_review_error(error)
        raise AssertionError("unreachable") from error
    return FieldReviewQueueViewRead.model_validate(view)


@router.get(
    "/kazakhstan/{code}/review",
    response_model=list[FieldReviewRecordRead],
)
async def list_field_review_records(
    code: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[FieldReviewRecordRead]:
    _ensure_supported_code(code)
    try:
        records = await KazakhstanOilGasFieldReviewService(session).list_pending(
            limit=limit,
            offset=offset,
        )
    except Exception as error:
        _raise_review_error(error)
        raise AssertionError("unreachable") from error

    return [
        FieldReviewRecordRead(
            record_id=record.record_id,
            external_id=record.external_id,
            raw_payload=record.raw_payload,
            normalized_payload=record.normalized_payload,
            status=record.status,
            links=[
                FieldReviewLinkRead(
                    link_id=link.link_id,
                    entity_id=link.entity_id,
                    entity_name_ru=link.entity_name_ru,
                    match_method=link.match_method,
                    match_confidence=link.match_confidence,
                    status=link.status,
                    verified_by=link.verified_by,
                    review_comment=link.review_comment,
                )
                for link in record.links
            ],
        )
        for record in records
    ]


@router.post(
    "/kazakhstan/{code}/review/{record_id}/links/{link_id}/confirm",
    response_model=FieldReviewActionResponse,
)
async def confirm_field_review_link(
    code: str,
    record_id: UUID,
    link_id: UUID,
    request: FieldReviewDecisionRequest,
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).confirm_link(
            record_id=record_id,
            link_id=link_id,
            reviewer=request.reviewer,
            comment=request.comment,
        )
    except Exception as error:
        _raise_review_error(error)
        raise AssertionError("unreachable") from error
    return _action_response(result)


@router.post(
    "/kazakhstan/{code}/review/{record_id}/links/{link_id}/reject",
    response_model=FieldReviewActionResponse,
)
async def reject_field_review_link(
    code: str,
    record_id: UUID,
    link_id: UUID,
    request: FieldReviewRejectRequest,
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).reject_link(
            record_id=record_id,
            link_id=link_id,
            reviewer=request.reviewer,
            comment=request.comment,
        )
    except Exception as error:
        _raise_review_error(error)
        raise AssertionError("unreachable") from error
    return _action_response(result)


@router.post(
    "/kazakhstan/{code}/review/{record_id}/manual-link",
    response_model=FieldReviewActionResponse,
)
async def manually_link_field_review_record(
    code: str,
    record_id: UUID,
    request: FieldReviewManualLinkRequest,
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).manual_link(
            record_id=record_id,
            entity_id=request.entity_id,
            reviewer=request.reviewer,
            comment=request.comment,
        )
    except Exception as error:
        _raise_review_error(error)
        raise AssertionError("unreachable") from error
    return _action_response(result)


@router.post(
    "/kazakhstan/{code}/review/{record_id}/create-draft-field",
    response_model=FieldReviewActionResponse,
)
async def create_draft_field_from_review_record(
    code: str,
    record_id: UUID,
    request: FieldReviewCreateDraftRequest,
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).create_draft_field(
            record_id=record_id,
            reviewer=request.reviewer,
            comment=request.comment,
            name_ru=request.name_ru,
            name_kk=request.name_kk,
            name_en=request.name_en,
        )
    except Exception as error:
        _raise_review_error(error)
        raise AssertionError("unreachable") from error
    return _action_response(result)
