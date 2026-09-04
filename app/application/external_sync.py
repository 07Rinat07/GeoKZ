from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import ResourceNotFoundError
from app.integrations.checksum import calculate_payload_checksum
from app.integrations.contracts import ExternalDataConnector
from app.integrations.errors import ConnectorConfigurationError
from app.integrations.types import ExternalRecordStatus, SyncRunStatus
from app.models.integration import ExternalDataSource, ExternalRecord, ExternalSyncRun


@dataclass(frozen=True, slots=True)
class SyncSummary:
    run_id: UUID
    source_id: UUID
    status: SyncRunStatus
    records_received: int
    records_created: int
    records_updated: int
    records_unchanged: int
    records_rejected: int


@dataclass(slots=True)
class ExternalSyncService:
    session: AsyncSession

    async def sync(
        self,
        source_id: UUID,
        connector: ExternalDataConnector,
    ) -> SyncSummary:
        source = await self.session.get(ExternalDataSource, source_id)
        if source is None:
            raise ResourceNotFoundError("Внешний источник данных не найден")
        if source.code != connector.source_code:
            raise ConnectorConfigurationError(
                "Код connector не соответствует зарегистрированному источнику GeoKZ"
            )
        if not source.enabled:
            raise ConnectorConfigurationError("Внешний источник отключён")

        started_at = datetime.now(UTC)
        source.last_sync_started_at = started_at
        source.last_error = None
        run = ExternalSyncRun(
            source_id=source.id,
            status=SyncRunStatus.RUNNING,
            started_at=started_at,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)

        received = 0
        created = 0
        updated = 0
        unchanged = 0
        rejected = 0

        try:
            dataset_version = await connector.get_dataset_version()
            async for envelope in connector.fetch_records(
                updated_since=source.last_success_at,
                cursor=source.cursor,
            ):
                received += 1
                checksum = calculate_payload_checksum(envelope.raw_payload)
                existing = await self.session.scalar(
                    select(ExternalRecord).where(
                        ExternalRecord.source_id == source.id,
                        ExternalRecord.record_type == envelope.record_type,
                        ExternalRecord.external_id == envelope.external_id,
                    )
                )

                if existing is None:
                    self.session.add(
                        ExternalRecord(
                            source_id=source.id,
                            external_id=envelope.external_id,
                            record_type=envelope.record_type,
                            language=envelope.language,
                            raw_payload=envelope.raw_payload,
                            checksum=checksum,
                            source_updated_at=envelope.source_updated_at,
                            retrieved_at=datetime.now(UTC),
                            status=ExternalRecordStatus.STAGED,
                        )
                    )
                    created += 1
                    continue

                existing.retrieved_at = datetime.now(UTC)
                existing.source_updated_at = envelope.source_updated_at
                if existing.checksum == checksum:
                    unchanged += 1
                    continue

                existing.raw_payload = envelope.raw_payload
                existing.normalized_payload = None
                existing.checksum = checksum
                existing.language = envelope.language
                existing.status = ExternalRecordStatus.CHANGED
                existing.is_deleted_upstream = False
                updated += 1

            completed_at = datetime.now(UTC)
            run.status = SyncRunStatus.SUCCESS
            run.finished_at = completed_at
            run.records_received = received
            run.records_created = created
            run.records_updated = updated
            run.records_unchanged = unchanged
            run.records_rejected = rejected
            source.dataset_version = dataset_version
            source.last_sync_completed_at = completed_at
            source.last_success_at = completed_at
            source.last_error_at = None
            source.last_error = None
            await self.session.commit()

            return SyncSummary(
                run_id=run.id,
                source_id=source.id,
                status=run.status,
                records_received=received,
                records_created=created,
                records_updated=updated,
                records_unchanged=unchanged,
                records_rejected=rejected,
            )
        except Exception as error:
            await self.session.rollback()
            failed_at = datetime.now(UTC)

            failed_run = await self.session.get(ExternalSyncRun, run.id)
            failed_source = await self.session.get(ExternalDataSource, source.id)
            if failed_run is not None:
                failed_run.status = SyncRunStatus.FAILED
                failed_run.finished_at = failed_at
                failed_run.records_received = received
                failed_run.records_created = created
                failed_run.records_updated = updated
                failed_run.records_unchanged = unchanged
                failed_run.records_rejected = rejected
                failed_run.error_message = str(error)
            if failed_source is not None:
                failed_source.last_sync_completed_at = failed_at
                failed_source.last_error_at = failed_at
                failed_source.last_error = str(error)
            await self.session.commit()
            raise
