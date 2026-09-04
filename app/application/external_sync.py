from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import ResourceNotFoundError
from app.integrations.checksum import calculate_payload_checksum
from app.integrations.contracts import ExternalDataConnector
from app.integrations.errors import (
    ConnectorConfigurationError,
    ExternalSyncAlreadyRunningError,
)
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
    running_timeout_hours: int = 6

    async def sync(
        self,
        source_id: UUID,
        connector: ExternalDataConnector,
    ) -> SyncSummary:
        source, run = await self._reserve_run(source_id, connector)

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
            run_id = run.id
            reserved_source_id = source.id
            await self.session.rollback()
            failed_at = datetime.now(UTC)

            failed_run = await self.session.get(ExternalSyncRun, run_id)
            failed_source = await self.session.get(ExternalDataSource, reserved_source_id)
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

    async def _reserve_run(
        self,
        source_id: UUID,
        connector: ExternalDataConnector,
    ) -> tuple[ExternalDataSource, ExternalSyncRun]:
        source = await self.session.get(ExternalDataSource, source_id)
        if source is None:
            raise ResourceNotFoundError("Внешний источник данных не найден")
        if source.code != connector.source_code:
            raise ConnectorConfigurationError(
                "Код connector не соответствует зарегистрированному источнику GeoKZ"
            )
        if not source.enabled:
            raise ConnectorConfigurationError("Внешний источник отключён")

        # Row-level lock serializes run reservation across API requests and the dedicated
        # scheduler process. The lock is held only for the short reservation transaction,
        # never for the external HTTP transfer itself.
        locked_source = await self.session.scalar(
            select(ExternalDataSource)
            .where(ExternalDataSource.id == source_id)
            .with_for_update()
        )
        if locked_source is None:
            await self.session.rollback()
            raise ResourceNotFoundError("Внешний источник данных не найден")

        started_at = datetime.now(UTC)
        stale_before = started_at - timedelta(hours=self.running_timeout_hours)
        stale_runs = list(
            await self.session.scalars(
                select(ExternalSyncRun).where(
                    ExternalSyncRun.source_id == source_id,
                    ExternalSyncRun.status == SyncRunStatus.RUNNING,
                    ExternalSyncRun.started_at < stale_before,
                )
            )
        )
        for stale_run in stale_runs:
            stale_run.status = SyncRunStatus.FAILED
            stale_run.finished_at = started_at
            stale_run.error_message = (
                "RUNNING sync автоматически помечен FAILED как stale после "
                f"{self.running_timeout_hours} ч. без завершения"
            )

        active_run = await self.session.scalar(
            select(ExternalSyncRun)
            .where(
                ExternalSyncRun.source_id == source_id,
                ExternalSyncRun.status == SyncRunStatus.RUNNING,
                ExternalSyncRun.started_at >= stale_before,
            )
            .order_by(ExternalSyncRun.started_at.desc())
            .limit(1)
        )
        if active_run is not None:
            # Rollback expires ORM state. Capture scalar identifiers first so constructing
            # the domain error never triggers implicit async IO after rollback.
            source_code = locked_source.code
            active_run_id = active_run.id
            await self.session.rollback()
            raise ExternalSyncAlreadyRunningError(source_code, active_run_id)

        locked_source.last_sync_started_at = started_at
        locked_source.last_error = None
        run = ExternalSyncRun(
            source_id=locked_source.id,
            status=SyncRunStatus.RUNNING,
            started_at=started_at,
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return locked_source, run
