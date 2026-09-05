from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.kazakhstan_field_processing import (
    OIL_GAS_FIELDS_RECORD_TYPE,
    OIL_GAS_FIELDS_SOURCE_CODE,
)
from app.integrations.types import (
    EntityLinkStatus,
    ExternalRecordStatus,
    MatchMethod,
)
from app.models.entity import GeologicalEntity
from app.models.enums import VerificationStatus
from app.models.integration import (
    ExternalDataSource,
    ExternalEntityLink,
    ExternalRecord,
)


class FieldReviewNotFoundError(LookupError):
    pass


class FieldReviewValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FieldReviewLink:
    link_id: UUID
    entity_id: UUID
    entity_name_ru: str
    entity_name_kk: str | None
    entity_name_en: str | None
    entity_verification_status: VerificationStatus
    match_method: MatchMethod
    match_confidence: float
    status: EntityLinkStatus
    verified_by: str | None
    review_comment: str | None


@dataclass(frozen=True, slots=True)
class FieldReviewRecord:
    record_id: UUID
    external_id: str
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None
    status: ExternalRecordStatus
    links: tuple[FieldReviewLink, ...]


@dataclass(frozen=True, slots=True)
class FieldReviewActionResult:
    record_id: UUID
    record_status: ExternalRecordStatus
    link_id: UUID
    link_status: EntityLinkStatus
    entity_id: UUID
    entity_verification_status: VerificationStatus


@dataclass(slots=True)
class KazakhstanOilGasFieldReviewService:
    session: AsyncSession

    async def count_pending(self) -> int:
        source = await self._get_source()
        count = await self.session.scalar(
            select(func.count(ExternalRecord.id)).where(
                ExternalRecord.source_id == source.id,
                ExternalRecord.record_type == OIL_GAS_FIELDS_RECORD_TYPE,
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
    ) -> list[FieldReviewRecord]:
        source = await self._get_source()
        records = list(
            await self.session.scalars(
                select(ExternalRecord)
                .where(
                    ExternalRecord.source_id == source.id,
                    ExternalRecord.record_type == OIL_GAS_FIELDS_RECORD_TYPE,
                    ExternalRecord.status == ExternalRecordStatus.REVIEW_REQUIRED,
                    ExternalRecord.is_deleted_upstream.is_(False),
                )
                .order_by(ExternalRecord.external_id)
                .limit(limit)
                .offset(offset)
            )
        )
        if not records:
            return []

        record_ids = [record.id for record in records]
        rows = (
            await self.session.execute(
                select(ExternalEntityLink, GeologicalEntity)
                .join(
                    GeologicalEntity,
                    GeologicalEntity.id == ExternalEntityLink.geological_entity_id,
                )
                .where(ExternalEntityLink.external_record_id.in_(record_ids))
            )
        ).all()
        links_by_record: dict[UUID, list[FieldReviewLink]] = {}
        for link, entity in rows:
            links_by_record.setdefault(link.external_record_id, []).append(
                FieldReviewLink(
                    link_id=link.id,
                    entity_id=entity.id,
                    entity_name_ru=entity.name_ru,
                    entity_name_kk=entity.name_kk,
                    entity_name_en=entity.name_en,
                    entity_verification_status=entity.verification_status,
                    match_method=link.match_method,
                    match_confidence=link.match_confidence,
                    status=link.status,
                    verified_by=link.verified_by,
                    review_comment=link.review_comment,
                )
            )

        return [
            FieldReviewRecord(
                record_id=record.id,
                external_id=record.external_id,
                raw_payload=record.raw_payload,
                normalized_payload=record.normalized_payload,
                status=record.status,
                links=tuple(links_by_record.get(record.id, [])),
            )
            for record in records
        ]

    async def confirm_link(
        self,
        *,
        record_id: UUID,
        link_id: UUID,
        reviewer: str,
        comment: str | None,
        commit: bool = True,
    ) -> FieldReviewActionResult:
        record, link, entity = await self._get_record_link_entity(record_id, link_id)
        await self._ensure_no_other_verified_link(record.id, except_link_id=link.id)

        reviewed_at = datetime.now(UTC)
        link.status = EntityLinkStatus.VERIFIED
        link.verified_by = reviewer
        link.verified_at = reviewed_at
        link.review_comment = comment
        await self._reject_other_unresolved_links(
            record.id,
            keep_link_id=link.id,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
        )
        record.status = ExternalRecordStatus.ACCEPTED
        if commit:
            await self.session.commit()
        return self._result(record, link, entity)

    async def reject_link(
        self,
        *,
        record_id: UUID,
        link_id: UUID,
        reviewer: str,
        comment: str,
        commit: bool = True,
    ) -> FieldReviewActionResult:
        record, link, entity = await self._get_record_link_entity(record_id, link_id)
        if link.status == EntityLinkStatus.VERIFIED:
            raise FieldReviewValidationError(
                "Подтверждённую связь нельзя отклонить этим действием; "
                "сначала требуется отдельная процедура пересмотра"
            )

        link.status = EntityLinkStatus.REJECTED
        link.verified_by = reviewer
        link.verified_at = datetime.now(UTC)
        link.review_comment = comment
        record.status = (
            ExternalRecordStatus.ACCEPTED
            if await self._has_verified_link(record.id)
            else ExternalRecordStatus.REVIEW_REQUIRED
        )
        if commit:
            await self.session.commit()
        return self._result(record, link, entity)

    async def manual_link(
        self,
        *,
        record_id: UUID,
        entity_id: UUID,
        reviewer: str,
        comment: str | None,
        commit: bool = True,
    ) -> FieldReviewActionResult:
        record = await self._get_record(record_id)
        entity = await self.session.get(GeologicalEntity, entity_id)
        if entity is None:
            raise FieldReviewNotFoundError("Геологический объект не найден")
        if entity.object_type.casefold() != "field":
            raise FieldReviewValidationError(
                "Запись нефтегазового месторождения можно связать только с object_type=field"
            )
        await self._ensure_no_other_verified_link(record.id)

        link = await self.session.scalar(
            select(ExternalEntityLink).where(
                ExternalEntityLink.external_record_id == record.id,
                ExternalEntityLink.geological_entity_id == entity.id,
            )
        )
        if link is None:
            link = ExternalEntityLink(
                external_record_id=record.id,
                geological_entity_id=entity.id,
                match_method=MatchMethod.MANUAL,
                match_confidence=1.0,
                status=EntityLinkStatus.VERIFIED,
            )
            self.session.add(link)
            await self.session.flush()

        reviewed_at = datetime.now(UTC)
        link.match_method = MatchMethod.MANUAL
        link.match_confidence = 1.0
        link.status = EntityLinkStatus.VERIFIED
        link.verified_by = reviewer
        link.verified_at = reviewed_at
        link.review_comment = comment
        await self._reject_other_unresolved_links(
            record.id,
            keep_link_id=link.id,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
        )
        record.status = ExternalRecordStatus.ACCEPTED
        if commit:
            await self.session.commit()
        return self._result(record, link, entity)

    async def create_draft_field(
        self,
        *,
        record_id: UUID,
        reviewer: str,
        comment: str | None,
        name_ru: str | None = None,
        name_kk: str | None = None,
        name_en: str | None = None,
        commit: bool = True,
    ) -> FieldReviewActionResult:
        record = await self._get_record(record_id)
        await self._ensure_no_other_verified_link(record.id)

        matching = (record.normalized_payload or {}).get("matching")
        matching_status = matching.get("status") if isinstance(matching, dict) else None
        if matching_status != "UNMATCHED":
            raise FieldReviewValidationError(
                "Новый DRAFT field можно создать только из записи со статусом matching=UNMATCHED"
            )

        normalized_name = (record.normalized_payload or {}).get("name_ru")
        selected_name = (name_ru or normalized_name or "").strip()
        if not selected_name:
            raise FieldReviewValidationError("Для нового DRAFT field требуется name_ru")

        source = await self._get_source()
        entity = GeologicalEntity(
            external_id=f"external-record:{record.id}",
            object_type="field",
            name_ru=selected_name,
            name_kk=name_kk.strip() if name_kk and name_kk.strip() else None,
            name_en=name_en.strip() if name_en and name_en.strip() else None,
            geological_context={
                "origin": "external_review_draft",
                "external_source_code": source.code,
                "external_record_id": str(record.id),
                "upstream_external_id": record.external_id,
            },
            verification_status=VerificationStatus.DRAFT,
        )
        self.session.add(entity)
        await self.session.flush()

        reviewed_at = datetime.now(UTC)
        link = ExternalEntityLink(
            external_record_id=record.id,
            geological_entity_id=entity.id,
            match_method=MatchMethod.MANUAL,
            match_confidence=1.0,
            status=EntityLinkStatus.VERIFIED,
            verified_by=reviewer,
            verified_at=reviewed_at,
            review_comment=comment,
        )
        self.session.add(link)
        await self.session.flush()
        await self._reject_other_unresolved_links(
            record.id,
            keep_link_id=link.id,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
        )
        record.status = ExternalRecordStatus.ACCEPTED
        if commit:
            await self.session.commit()
        return self._result(record, link, entity)

    async def _get_source(self) -> ExternalDataSource:
        source = await self.session.scalar(
            select(ExternalDataSource).where(
                ExternalDataSource.code == OIL_GAS_FIELDS_SOURCE_CODE
            )
        )
        if source is None:
            raise FieldReviewNotFoundError(
                "Источник нефтегазовых месторождений не зарегистрирован"
            )
        return source

    async def _get_record(self, record_id: UUID) -> ExternalRecord:
        source = await self._get_source()
        record = await self.session.scalar(
            select(ExternalRecord).where(
                ExternalRecord.id == record_id,
                ExternalRecord.source_id == source.id,
                ExternalRecord.record_type == OIL_GAS_FIELDS_RECORD_TYPE,
            )
        )
        if record is None:
            raise FieldReviewNotFoundError("Внешняя запись месторождения не найдена")
        return record

    async def _get_record_link_entity(
        self,
        record_id: UUID,
        link_id: UUID,
    ) -> tuple[ExternalRecord, ExternalEntityLink, GeologicalEntity]:
        record = await self._get_record(record_id)
        link = await self.session.scalar(
            select(ExternalEntityLink).where(
                ExternalEntityLink.id == link_id,
                ExternalEntityLink.external_record_id == record.id,
            )
        )
        if link is None:
            raise FieldReviewNotFoundError("Кандидат связи не найден")
        entity = await self.session.get(GeologicalEntity, link.geological_entity_id)
        if entity is None:
            raise FieldReviewNotFoundError("Связанный геологический объект не найден")
        return record, link, entity

    async def _ensure_no_other_verified_link(
        self,
        record_id: UUID,
        *,
        except_link_id: UUID | None = None,
    ) -> None:
        statement = select(ExternalEntityLink).where(
            ExternalEntityLink.external_record_id == record_id,
            ExternalEntityLink.status == EntityLinkStatus.VERIFIED,
        )
        if except_link_id is not None:
            statement = statement.where(ExternalEntityLink.id != except_link_id)
        if await self.session.scalar(statement) is not None:
            raise FieldReviewValidationError(
                "У записи уже есть другая VERIFIED связь; сначала требуется её пересмотр"
            )

    async def _has_verified_link(self, record_id: UUID) -> bool:
        return (
            await self.session.scalar(
                select(ExternalEntityLink.id).where(
                    ExternalEntityLink.external_record_id == record_id,
                    ExternalEntityLink.status == EntityLinkStatus.VERIFIED,
                )
            )
            is not None
        )

    async def _reject_other_unresolved_links(
        self,
        record_id: UUID,
        *,
        keep_link_id: UUID,
        reviewer: str,
        reviewed_at: datetime,
    ) -> None:
        links = list(
            await self.session.scalars(
                select(ExternalEntityLink).where(
                    ExternalEntityLink.external_record_id == record_id,
                    ExternalEntityLink.id != keep_link_id,
                    ExternalEntityLink.status.in_(
                        (EntityLinkStatus.REVIEW_REQUIRED, EntityLinkStatus.AUTO_MATCHED)
                    ),
                )
            )
        )
        for link in links:
            link.status = EntityLinkStatus.REJECTED
            link.verified_by = reviewer
            link.verified_at = reviewed_at
            if not link.review_comment:
                link.review_comment = "Отклонено при подтверждении другой связи"

    @staticmethod
    def _result(
        record: ExternalRecord,
        link: ExternalEntityLink,
        entity: GeologicalEntity,
    ) -> FieldReviewActionResult:
        return FieldReviewActionResult(
            record_id=record.id,
            record_status=record.status,
            link_id=link.id,
            link_status=link.status,
            entity_id=entity.id,
            entity_verification_status=entity.verification_status,
        )
