from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.kazakhstan_license_processing import (
    GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
    GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE,
)
from app.integrations.types import ExternalRecordStatus
from app.models.integration import ExternalDataSource, ExternalRecord


class LicenseReviewNotFoundError(LookupError):
    pass


class LicenseReviewValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LicenseReviewRecord:
    record_id: UUID
    external_id: str
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None
    status: ExternalRecordStatus
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_comment: str | None


@dataclass(frozen=True, slots=True)
class LicenseReviewActionResult:
    record_id: UUID
    record_status: ExternalRecordStatus
    reviewed_by: str
    reviewed_at: datetime
    review_comment: str | None


@dataclass(slots=True)
class KazakhstanGeologicalStudyLicenseReviewService:
    """Human review for administrative license records.

    This workflow intentionally reviews the external record itself. It does not create a
    GeologicalEntity or ExternalEntityLink because the verified v6 dataset card does not
    expose a stable geological object/geometry identifier suitable for deterministic
    matching.
    """

    session: AsyncSession

    async def count_pending(self) -> int:
        source = await self._get_source()
        count = await self.session.scalar(
            select(func.count(ExternalRecord.id)).where(
                ExternalRecord.source_id == source.id,
                ExternalRecord.record_type == GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
                ExternalRecord.status == ExternalRecordStatus.REVIEW_REQUIRED,
                ExternalRecord.is_deleted_upstream.is_(False),
            )
        )
        return int(count or 0)

    async def list_pending(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LicenseReviewRecord]:
        source = await self._get_source()
        records = list(
            await self.session.scalars(
                select(ExternalRecord)
                .where(
                    ExternalRecord.source_id == source.id,
                    ExternalRecord.record_type == GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
                    ExternalRecord.status == ExternalRecordStatus.REVIEW_REQUIRED,
                    ExternalRecord.is_deleted_upstream.is_(False),
                )
                .order_by(ExternalRecord.external_id)
                .limit(limit)
                .offset(offset)
            )
        )
        return [self._to_record(record) for record in records]

    async def accept(
        self,
        *,
        record_id: UUID,
        reviewer: str,
        comment: str | None,
    ) -> LicenseReviewActionResult:
        record = await self._get_record(record_id)
        if record.status != ExternalRecordStatus.REVIEW_REQUIRED:
            raise LicenseReviewValidationError(
                "Принять можно только запись со статусом REVIEW_REQUIRED"
            )
        normalized = record.normalized_payload or {}
        if normalized.get("normalization_status") != "NORMALIZED":
            raise LicenseReviewValidationError(
                "Запись с ошибкой нормализации нельзя принять; сначала исправьте mapping/normalizer"
            )

        reviewed_at = datetime.now(UTC)
        record.status = ExternalRecordStatus.ACCEPTED
        record.reviewed_by = reviewer
        record.reviewed_at = reviewed_at
        record.review_comment = comment
        record.normalized_payload = {
            **normalized,
            "review": {
                **self._existing_review(normalized),
                "status": "ACCEPTED",
                "reviewed_by": reviewer,
                "reviewed_at": reviewed_at.isoformat(),
            },
        }
        await self.session.commit()
        return self._result(record)

    async def reject(
        self,
        *,
        record_id: UUID,
        reviewer: str,
        comment: str,
    ) -> LicenseReviewActionResult:
        record = await self._get_record(record_id)
        if record.status != ExternalRecordStatus.REVIEW_REQUIRED:
            raise LicenseReviewValidationError(
                "Отклонить можно только запись со статусом REVIEW_REQUIRED"
            )

        reviewed_at = datetime.now(UTC)
        normalized = record.normalized_payload or {
            "schema_version": 1,
            "record_type": GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
        }
        record.status = ExternalRecordStatus.REJECTED
        record.reviewed_by = reviewer
        record.reviewed_at = reviewed_at
        record.review_comment = comment
        record.normalized_payload = {
            **normalized,
            "review": {
                **self._existing_review(normalized),
                "status": "REJECTED",
                "reviewed_by": reviewer,
                "reviewed_at": reviewed_at.isoformat(),
                "comment": comment,
            },
        }
        await self.session.commit()
        return self._result(record)

    async def _get_source(self) -> ExternalDataSource:
        source = await self.session.scalar(
            select(ExternalDataSource).where(
                ExternalDataSource.code == GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE
            )
        )
        if source is None:
            raise LicenseReviewNotFoundError(
                "Источник лицензий на геологическое изучение недр не зарегистрирован"
            )
        return source

    async def _get_record(self, record_id: UUID) -> ExternalRecord:
        source = await self._get_source()
        record = await self.session.scalar(
            select(ExternalRecord).where(
                ExternalRecord.id == record_id,
                ExternalRecord.source_id == source.id,
                ExternalRecord.record_type == GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
                ExternalRecord.is_deleted_upstream.is_(False),
            )
        )
        if record is None:
            raise LicenseReviewNotFoundError("Внешняя запись лицензии не найдена")
        return record

    @staticmethod
    def _existing_review(normalized: dict[str, Any]) -> dict[str, Any]:
        review = normalized.get("review")
        return dict(review) if isinstance(review, dict) else {}

    @staticmethod
    def _to_record(record: ExternalRecord) -> LicenseReviewRecord:
        return LicenseReviewRecord(
            record_id=record.id,
            external_id=record.external_id,
            raw_payload=record.raw_payload,
            normalized_payload=record.normalized_payload,
            status=record.status,
            reviewed_by=record.reviewed_by,
            reviewed_at=record.reviewed_at,
            review_comment=record.review_comment,
        )

    @staticmethod
    def _result(record: ExternalRecord) -> LicenseReviewActionResult:
        assert record.reviewed_by is not None
        assert record.reviewed_at is not None
        return LicenseReviewActionResult(
            record_id=record.id,
            record_status=record.status,
            reviewed_by=record.reviewed_by,
            reviewed_at=record.reviewed_at,
            review_comment=record.review_comment,
        )
