from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.errors import ExternalSourceProtocolError
from app.integrations.normalizers.kazakhstan_geological_study_licenses import (
    normalize_geological_study_license_record,
)
from app.integrations.types import ExternalRecordStatus
from app.models.integration import ExternalDataSource, ExternalRecord

GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE = "kz-egov-geological-study-licenses"
GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE = "geological_study_license"


@dataclass(frozen=True, slots=True)
class GeologicalStudyLicenseProcessingSummary:
    source_id: UUID
    processed: int
    normalized: int
    exact_matches: int
    alias_matches: int
    ambiguous: int
    unmatched: int
    normalization_errors: int
    reviewer_locked: int
    review_required: int


@dataclass(slots=True)
class KazakhstanGeologicalStudyLicenseProcessingService:
    """Normalize official license records without inventing geological entity links.

    The current upstream dataset exposes administrative license attributes but no stable
    field/deposit geometry or geological-object identifier. Therefore processing stops at
    record-level review instead of creating low-confidence ExternalEntityLink rows.
    """

    session: AsyncSession

    async def process(self) -> GeologicalStudyLicenseProcessingSummary:
        source = await self.session.scalar(
            select(ExternalDataSource).where(
                ExternalDataSource.code == GEOLOGICAL_STUDY_LICENSES_SOURCE_CODE
            )
        )
        if source is None:
            raise LookupError(
                "Источник лицензий на геологическое изучение недр не зарегистрирован; "
                "сначала выполните /integrations/kazakhstan/register"
            )

        records = list(
            await self.session.scalars(
                select(ExternalRecord)
                .where(
                    ExternalRecord.source_id == source.id,
                    ExternalRecord.record_type == GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
                    ExternalRecord.is_deleted_upstream.is_(False),
                    ExternalRecord.status.in_(
                        (
                            ExternalRecordStatus.STAGED,
                            ExternalRecordStatus.CHANGED,
                            ExternalRecordStatus.REVIEW_REQUIRED,
                        )
                    ),
                )
                .order_by(ExternalRecord.external_id)
            )
        )

        normalized_count = 0
        normalization_errors = 0
        reviewer_locked = 0
        review_required = 0

        for record in records:
            if self._review_is_locked(record):
                reviewer_locked += 1
                continue

            # A changed upstream payload invalidates the previous record-level review.
            if record.status == ExternalRecordStatus.CHANGED:
                record.reviewed_by = None
                record.reviewed_at = None
                record.review_comment = None

            try:
                normalized = normalize_geological_study_license_record(record.raw_payload)
            except ExternalSourceProtocolError as error:
                normalization_errors += 1
                review_required += 1
                record.status = ExternalRecordStatus.REVIEW_REQUIRED
                record.normalized_payload = {
                    "schema_version": 1,
                    "record_type": GEOLOGICAL_STUDY_LICENSES_RECORD_TYPE,
                    "normalization_status": "ERROR",
                    "normalization_error": str(error),
                    "review": {
                        "status": "PENDING",
                        "entity_matching": "NOT_APPLICABLE",
                    },
                }
                continue

            normalized_count += 1
            review_required += 1
            record.status = ExternalRecordStatus.REVIEW_REQUIRED
            record.normalized_payload = {
                **normalized.as_payload(),
                "normalization_status": "NORMALIZED",
                "review": {
                    "status": "PENDING",
                    "entity_matching": "NOT_APPLICABLE",
                    "reason": (
                        "Upstream license register has no stable geological object/geometry "
                        "identifier in the verified v6 dataset card; expert record review is required"
                    ),
                },
            }

        await self.session.commit()
        return GeologicalStudyLicenseProcessingSummary(
            source_id=source.id,
            processed=len(records),
            normalized=normalized_count,
            exact_matches=0,
            alias_matches=0,
            ambiguous=0,
            unmatched=0,
            normalization_errors=normalization_errors,
            reviewer_locked=reviewer_locked,
            review_required=review_required,
        )

    @staticmethod
    def _review_is_locked(record: ExternalRecord) -> bool:
        return (
            record.status in (ExternalRecordStatus.ACCEPTED, ExternalRecordStatus.REJECTED)
            and bool(record.reviewed_by)
            and record.reviewed_at is not None
        )
