from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.errors import ExternalSourceProtocolError
from app.integrations.normalizers.kazakhstan_oil_gas_fields import (
    normalize_entity_name,
    normalize_oil_gas_field_record,
)
from app.integrations.types import (
    EntityLinkStatus,
    ExternalRecordStatus,
    MatchMethod,
)
from app.models.entity import EntityName, GeologicalEntity
from app.models.integration import ExternalDataSource, ExternalEntityLink, ExternalRecord


OIL_GAS_FIELDS_SOURCE_CODE = "kz-egov-oil-gas-fields"
OIL_GAS_FIELDS_RECORD_TYPE = "oil_gas_field"


@dataclass(frozen=True, slots=True)
class OilGasFieldProcessingSummary:
    source_id: UUID
    processed: int
    normalized: int
    exact_matches: int
    alias_matches: int
    ambiguous: int
    unmatched: int
    normalization_errors: int
    reviewer_locked: int


@dataclass(slots=True)
class KazakhstanOilGasFieldProcessingService:
    session: AsyncSession

    async def process(self) -> OilGasFieldProcessingSummary:
        source = await self.session.scalar(
            select(ExternalDataSource).where(
                ExternalDataSource.code == OIL_GAS_FIELDS_SOURCE_CODE
            )
        )
        if source is None:
            raise LookupError(
                "Источник нефтегазовых месторождений не зарегистрирован; "
                "сначала выполните /integrations/kazakhstan/register"
            )

        records = list(
            await self.session.scalars(
                select(ExternalRecord)
                .where(
                    ExternalRecord.source_id == source.id,
                    ExternalRecord.record_type == OIL_GAS_FIELDS_RECORD_TYPE,
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

        name_index = await self._build_field_name_index()
        links_by_record = await self._load_links(records)

        normalized_count = 0
        exact_matches = 0
        alias_matches = 0
        ambiguous = 0
        unmatched = 0
        normalization_errors = 0
        reviewer_locked = 0

        for record in records:
            existing_links = links_by_record.get(record.id, [])
            locked = [link for link in existing_links if self._is_reviewer_locked(link)]

            try:
                normalized = normalize_oil_gas_field_record(record.raw_payload)
            except ExternalSourceProtocolError as error:
                normalization_errors += 1
                if locked:
                    reviewer_locked += 1
                else:
                    await self._clear_automatic_links(existing_links)
                record.status = (
                    ExternalRecordStatus.ACCEPTED
                    if any(link.status == EntityLinkStatus.VERIFIED for link in locked)
                    else ExternalRecordStatus.REVIEW_REQUIRED
                )
                record.normalized_payload = {
                    "schema_version": 1,
                    "entity_type": "field",
                    "normalization_status": "ERROR",
                    "normalization_error": str(error),
                    "matching": {
                        "status": "REVIEWER_LOCKED" if locked else "UNAVAILABLE",
                        "linked_entity_ids": [
                            str(link.geological_entity_id) for link in locked
                        ],
                    },
                }
                continue

            normalized_count += 1
            candidates = name_index.get(normalized.match_key, [])
            payload = normalized.as_payload()

            if locked:
                reviewer_locked += 1
                record.status = (
                    ExternalRecordStatus.ACCEPTED
                    if any(link.status == EntityLinkStatus.VERIFIED for link in locked)
                    else ExternalRecordStatus.REVIEW_REQUIRED
                )
                record.normalized_payload = {
                    **payload,
                    "matching": {
                        "status": "REVIEWER_LOCKED",
                        "linked_entity_ids": [
                            str(link.geological_entity_id) for link in locked
                        ],
                    },
                }
                continue

            await self._clear_automatic_links(existing_links)

            unique_candidates: dict[UUID, MatchMethod] = {}
            for entity_id, method in candidates:
                previous = unique_candidates.get(entity_id)
                if previous is None or method == MatchMethod.EXACT_NAME:
                    unique_candidates[entity_id] = method

            if not unique_candidates:
                unmatched += 1
                record.status = ExternalRecordStatus.REVIEW_REQUIRED
                record.normalized_payload = {
                    **payload,
                    "matching": {"status": "UNMATCHED", "candidate_entity_ids": []},
                }
                continue

            if len(unique_candidates) > 1:
                ambiguous += 1
                record.status = ExternalRecordStatus.REVIEW_REQUIRED
                record.normalized_payload = {
                    **payload,
                    "matching": {
                        "status": "AMBIGUOUS",
                        "candidate_entity_ids": [
                            str(entity_id) for entity_id in unique_candidates
                        ],
                    },
                }
                continue

            entity_id, method = next(iter(unique_candidates.items()))
            if method == MatchMethod.EXACT_NAME:
                exact_matches += 1
            else:
                alias_matches += 1

            self.session.add(
                ExternalEntityLink(
                    external_record_id=record.id,
                    geological_entity_id=entity_id,
                    match_method=method,
                    match_confidence=1.0,
                    status=EntityLinkStatus.REVIEW_REQUIRED,
                )
            )
            record.status = ExternalRecordStatus.REVIEW_REQUIRED
            record.normalized_payload = {
                **payload,
                "matching": {
                    "status": "CANDIDATE",
                    "candidate_entity_ids": [str(entity_id)],
                    "match_method": method.value,
                    "confidence": 1.0,
                },
            }

        await self.session.commit()
        return OilGasFieldProcessingSummary(
            source_id=source.id,
            processed=len(records),
            normalized=normalized_count,
            exact_matches=exact_matches,
            alias_matches=alias_matches,
            ambiguous=ambiguous,
            unmatched=unmatched,
            normalization_errors=normalization_errors,
            reviewer_locked=reviewer_locked,
        )

    async def _build_field_name_index(self) -> dict[str, list[tuple[UUID, MatchMethod]]]:
        entities = list(
            await self.session.scalars(
                select(GeologicalEntity).where(
                    func.lower(GeologicalEntity.object_type) == "field"
                )
            )
        )
        index: dict[str, list[tuple[UUID, MatchMethod]]] = {}
        for entity in entities:
            for value in (entity.name_ru, entity.name_kk, entity.name_en):
                self._add_to_index(index, value, entity.id, MatchMethod.EXACT_NAME)

        entity_ids = [entity.id for entity in entities]
        if not entity_ids:
            return index

        names = list(
            await self.session.scalars(
                select(EntityName).where(EntityName.entity_id.in_(entity_ids))
            )
        )
        for name in names:
            self._add_to_index(index, name.name, name.entity_id, MatchMethod.ALIAS)
        return index

    async def _load_links(
        self,
        records: list[ExternalRecord],
    ) -> dict[UUID, list[ExternalEntityLink]]:
        record_ids = [record.id for record in records]
        if not record_ids:
            return {}
        links = list(
            await self.session.scalars(
                select(ExternalEntityLink).where(
                    ExternalEntityLink.external_record_id.in_(record_ids)
                )
            )
        )
        result: dict[UUID, list[ExternalEntityLink]] = {}
        for link in links:
            result.setdefault(link.external_record_id, []).append(link)
        return result

    async def _clear_automatic_links(
        self,
        links: list[ExternalEntityLink],
    ) -> None:
        for link in links:
            if not self._is_reviewer_locked(link):
                await self.session.delete(link)

    @staticmethod
    def _is_reviewer_locked(link: ExternalEntityLink) -> bool:
        return (
            link.status in (EntityLinkStatus.VERIFIED, EntityLinkStatus.REJECTED)
            or link.match_method == MatchMethod.MANUAL
            or bool(link.verified_by)
            or bool(link.review_comment and link.review_comment.strip())
        )

    @staticmethod
    def _add_to_index(
        index: dict[str, list[tuple[UUID, MatchMethod]]],
        value: str | None,
        entity_id: UUID,
        method: MatchMethod,
    ) -> None:
        if not value or not value.strip():
            return
        key = normalize_entity_name(value)
        if key:
            index.setdefault(key, []).append((entity_id, method))
