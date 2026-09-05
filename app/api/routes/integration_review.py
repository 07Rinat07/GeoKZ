from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import (
    CurrentPrincipal,
    get_current_principal,
    require_expert,
)
from app.application.audit import AuditActor, AuditRevisionService
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
from app.application.kazakhstan_license_processing import (
    GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE,
)
from app.application.kazakhstan_license_review import (
    KazakhstanGeologicalStudyLicenseReviewService,
    LicenseReviewNotFoundError,
    LicenseReviewValidationError,
)
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.models.entity import GeologicalEntity
from app.models.enums import AuditAction
from app.schemas.entity import GeologicalEntityRead
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
from app.schemas.license_review import (
    LicenseReviewActionResponse,
    LicenseReviewDecisionRequest,
    LicenseReviewRecordRead,
    LicenseReviewRejectRequest,
)

router = APIRouter()


def _ensure_supported_code(code: str) -> None:
    if code != OIL_GAS_FIELDS_SOURCE_CODE:
        raise HTTPException(
            status_code=422,
            detail="Review workflow сопоставления пока реализован только для нефтегазовых месторождений",
        )


def _ensure_license_code(code: str) -> None:
    if code != GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE:
        raise HTTPException(
            status_code=422,
            detail="Record-level review доступен только для реестра лицензий на геологическое изучение недр",
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


def _raise_license_review_error(error: Exception) -> None:
    if isinstance(error, LicenseReviewNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, LicenseReviewValidationError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    raise error


async def _audit_field_review(
    session: AsyncSession,
    *,
    principal: CurrentPrincipal,
    action_code: str,
    result: FieldReviewActionResult,
    comment: str | None,
) -> None:
    await AuditRevisionService(session).append_audit(
        actor=AuditActor.from_user(principal.user),
        action=AuditAction.REVIEW,
        resource_type="external_field_review",
        resource_id=result.record_id,
        reason=action_code,
        details={
            "link_id": str(result.link_id),
            "entity_id": str(result.entity_id),
            "link_status": result.link_status.value,
            "record_status": result.record_status.value,
            "comment": comment,
        },
    )


async def _audit_created_draft_entity(
    session: AsyncSession,
    *,
    principal: CurrentPrincipal,
    entity_id: UUID,
    comment: str | None,
) -> None:
    entity = await session.get(GeologicalEntity, entity_id)
    if entity is None:
        raise RuntimeError("Draft entity created by review service cannot be reloaded")
    await session.refresh(entity)
    await AuditRevisionService(session).audit_master_change(
        actor=AuditActor.from_user(principal.user),
        action=AuditAction.CREATE,
        resource_type="geological_entity",
        resource_id=entity.id,
        snapshot=GeologicalEntityRead.model_validate(entity).model_dump(mode="json"),
        reason="external_review_create_draft",
        details={"review_comment": comment},
    )


@router.get(
    "/kazakhstan/{code}/review/view",
    response_model=FieldReviewQueueViewRead,
)
async def get_field_review_queue_view(
    code: str,
    lang: SupportedLanguage = Query(default="ru"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _principal: CurrentPrincipal = Depends(get_current_principal),
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
    _principal: CurrentPrincipal = Depends(get_current_principal),
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
    principal: CurrentPrincipal = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).confirm_link(
            record_id=record_id,
            link_id=link_id,
            reviewer=principal.user.username,
            comment=request.comment,
            commit=False,
        )
        await _audit_field_review(
            session,
            principal=principal,
            action_code="CONFIRM_LINK",
            result=result,
            comment=request.comment,
        )
        await session.commit()
    except Exception as error:
        await session.rollback()
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
    principal: CurrentPrincipal = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).reject_link(
            record_id=record_id,
            link_id=link_id,
            reviewer=principal.user.username,
            comment=request.comment,
            commit=False,
        )
        await _audit_field_review(
            session,
            principal=principal,
            action_code="REJECT_LINK",
            result=result,
            comment=request.comment,
        )
        await session.commit()
    except Exception as error:
        await session.rollback()
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
    principal: CurrentPrincipal = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).manual_link(
            record_id=record_id,
            entity_id=request.entity_id,
            reviewer=principal.user.username,
            comment=request.comment,
            commit=False,
        )
        await _audit_field_review(
            session,
            principal=principal,
            action_code="MANUAL_LINK",
            result=result,
            comment=request.comment,
        )
        await session.commit()
    except Exception as error:
        await session.rollback()
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
    principal: CurrentPrincipal = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
) -> FieldReviewActionResponse:
    _ensure_supported_code(code)
    try:
        result = await KazakhstanOilGasFieldReviewService(session).create_draft_field(
            record_id=record_id,
            reviewer=principal.user.username,
            comment=request.comment,
            name_ru=request.name_ru,
            name_kk=request.name_kk,
            name_en=request.name_en,
            commit=False,
        )
        await _audit_created_draft_entity(
            session,
            principal=principal,
            entity_id=result.entity_id,
            comment=request.comment,
        )
        await _audit_field_review(
            session,
            principal=principal,
            action_code="CREATE_DRAFT_FIELD",
            result=result,
            comment=request.comment,
        )
        await session.commit()
    except Exception as error:
        await session.rollback()
        _raise_review_error(error)
        raise AssertionError("unreachable") from error
    return _action_response(result)


@router.get(
    "/kazakhstan/{code}/review/records",
    response_model=list[LicenseReviewRecordRead],
)
async def list_license_review_records(
    code: str,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> list[LicenseReviewRecordRead]:
    _ensure_license_code(code)
    try:
        records = await KazakhstanGeologicalStudyLicenseReviewService(
            session
        ).list_pending(limit=limit, offset=offset)
    except Exception as error:
        _raise_license_review_error(error)
        raise AssertionError("unreachable") from error
    return [LicenseReviewRecordRead.model_validate(record) for record in records]


@router.post(
    "/kazakhstan/{code}/review/records/{record_id}/accept",
    response_model=LicenseReviewActionResponse,
)
async def accept_license_review_record(
    code: str,
    record_id: UUID,
    request: LicenseReviewDecisionRequest,
    principal: CurrentPrincipal = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
) -> LicenseReviewActionResponse:
    _ensure_license_code(code)
    try:
        result = await KazakhstanGeologicalStudyLicenseReviewService(session).accept(
            record_id=record_id,
            reviewer=principal.user.username,
            comment=request.comment,
            commit=False,
        )
        await AuditRevisionService(session).append_audit(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.REVIEW,
            resource_type="external_license_review",
            resource_id=record_id,
            reason="ACCEPT",
            details={"record_status": result.record_status.value, "comment": request.comment},
        )
        await session.commit()
    except Exception as error:
        await session.rollback()
        _raise_license_review_error(error)
        raise AssertionError("unreachable") from error
    return LicenseReviewActionResponse.model_validate(result)


@router.post(
    "/kazakhstan/{code}/review/records/{record_id}/reject",
    response_model=LicenseReviewActionResponse,
)
async def reject_license_review_record(
    code: str,
    record_id: UUID,
    request: LicenseReviewRejectRequest,
    principal: CurrentPrincipal = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
) -> LicenseReviewActionResponse:
    _ensure_license_code(code)
    try:
        result = await KazakhstanGeologicalStudyLicenseReviewService(session).reject(
            record_id=record_id,
            reviewer=principal.user.username,
            comment=request.comment,
            commit=False,
        )
        await AuditRevisionService(session).append_audit(
            actor=AuditActor.from_user(principal.user),
            action=AuditAction.REVIEW,
            resource_type="external_license_review",
            resource_id=record_id,
            reason="REJECT",
            details={"record_status": result.record_status.value, "comment": request.comment},
        )
        await session.commit()
    except Exception as error:
        await session.rollback()
        _raise_license_review_error(error)
        raise AssertionError("unreachable") from error
    return LicenseReviewActionResponse.model_validate(result)
