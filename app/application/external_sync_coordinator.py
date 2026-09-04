from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.external_sync import ExternalSyncService, SyncSummary
from app.core.config import Settings
from app.integrations.errors import (
    ExternalConnectorNotSupportedError,
    ExternalSyncAlreadyRunningError,
)
from app.integrations.registry import ExternalConnectorRegistry
from app.integrations.types import (
    SyncBatchMode,
    SyncDispatchStatus,
    SyncMode,
    SyncRunStatus,
)
from app.models.integration import ExternalDataSource, ExternalSyncRun


@dataclass(frozen=True, slots=True)
class ExternalSourceScheduleStatus:
    source_id: UUID
    source_code: str
    enabled: bool
    sync_mode: SyncMode
    sync_interval_hours: int
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None
    next_due_at: datetime | None
    due: bool
    running_run_id: UUID | None


@dataclass(frozen=True, slots=True)
class ExternalSyncDispatchResult:
    source_id: UUID
    source_code: str
    dispatch_status: SyncDispatchStatus
    run_id: UUID | None
    sync_status: SyncRunStatus | None
    records_received: int
    records_created: int
    records_updated: int
    records_unchanged: int
    records_rejected: int
    next_due_at: datetime | None
    error: str | None


@dataclass(frozen=True, slots=True)
class ExternalSyncBatchSummary:
    mode: SyncBatchMode
    started_at: datetime
    finished_at: datetime
    total_sources: int
    attempted: int
    succeeded: int
    failed: int
    already_running: int
    skipped: int
    results: tuple[ExternalSyncDispatchResult, ...]


def calculate_next_due_at(
    source: ExternalDataSource,
    *,
    failure_retry_hours: int,
) -> datetime | None:
    if not source.enabled or source.sync_mode != SyncMode.AUTOMATIC:
        return None

    if source.last_error_at is not None and (
        source.last_success_at is None or source.last_error_at >= source.last_success_at
    ):
        retry_hours = min(source.sync_interval_hours, failure_retry_hours)
        return source.last_error_at + timedelta(hours=retry_hours)

    anchor = source.last_success_at or source.last_sync_completed_at
    if anchor is None:
        # None means "due immediately" for a never-synchronized automatic source.
        return None
    return anchor + timedelta(hours=source.sync_interval_hours)


def is_source_due(
    source: ExternalDataSource,
    *,
    now: datetime,
    failure_retry_hours: int,
) -> bool:
    if not source.enabled or source.sync_mode != SyncMode.AUTOMATIC:
        return False
    if (
        source.last_success_at is None
        and source.last_sync_completed_at is None
        and source.last_error_at is None
    ):
        return True
    next_due_at = calculate_next_due_at(
        source,
        failure_retry_hours=failure_retry_hours,
    )
    return next_due_at is not None and next_due_at <= now


@dataclass(slots=True)
class ExternalSyncCoordinator:
    session: AsyncSession
    settings: Settings

    async def schedule_status(self) -> list[ExternalSourceScheduleStatus]:
        now = datetime.now(UTC)
        sources = list(
            await self.session.scalars(
                select(ExternalDataSource).order_by(ExternalDataSource.code)
            )
        )
        running = await self._running_runs_by_source()
        return [
            ExternalSourceScheduleStatus(
                source_id=source.id,
                source_code=source.code,
                enabled=source.enabled,
                sync_mode=source.sync_mode,
                sync_interval_hours=source.sync_interval_hours,
                last_success_at=source.last_success_at,
                last_error_at=source.last_error_at,
                last_error=source.last_error,
                next_due_at=calculate_next_due_at(
                    source,
                    failure_retry_hours=self.settings.external_sync_failure_retry_hours,
                ),
                due=is_source_due(
                    source,
                    now=now,
                    failure_retry_hours=self.settings.external_sync_failure_retry_hours,
                ),
                running_run_id=running.get(source.id),
            )
            for source in sources
        ]

    async def sync_all(self) -> ExternalSyncBatchSummary:
        return await self._run_batch(SyncBatchMode.MANUAL_ALL)

    async def sync_due(self) -> ExternalSyncBatchSummary:
        return await self._run_batch(SyncBatchMode.SCHEDULED_DUE)

    async def _run_batch(self, mode: SyncBatchMode) -> ExternalSyncBatchSummary:
        started_at = datetime.now(UTC)
        sources = list(
            await self.session.scalars(
                select(ExternalDataSource).order_by(ExternalDataSource.code)
            )
        )
        registry = ExternalConnectorRegistry(self.settings)
        results: list[ExternalSyncDispatchResult] = []

        for source in sources:
            skip_status = self._skip_status(source, mode, started_at)
            if skip_status is not None:
                results.append(
                    self._empty_result(
                        source,
                        dispatch_status=skip_status,
                        error=None,
                    )
                )
                continue

            try:
                connector = registry.build(source.code)
            except ExternalConnectorNotSupportedError as error:
                results.append(
                    self._empty_result(
                        source,
                        dispatch_status=SyncDispatchStatus.SKIPPED_UNSUPPORTED,
                        error=str(error),
                    )
                )
                continue

            try:
                summary = await ExternalSyncService(
                    self.session,
                    running_timeout_hours=(
                        self.settings.external_sync_running_timeout_hours
                    ),
                ).sync(source.id, connector)
            except ExternalSyncAlreadyRunningError as error:
                results.append(
                    self._empty_result(
                        source,
                        dispatch_status=SyncDispatchStatus.ALREADY_RUNNING,
                        error=str(error),
                        run_id=error.run_id,
                        sync_status=SyncRunStatus.RUNNING,
                    )
                )
                continue
            except Exception as error:
                await self.session.rollback()
                refreshed = await self.session.get(ExternalDataSource, source.id)
                if refreshed is not None:
                    source = refreshed
                results.append(
                    self._empty_result(
                        source,
                        dispatch_status=SyncDispatchStatus.FAILED,
                        error=str(error),
                    )
                )
                continue

            results.append(self._success_result(source, summary))

        finished_at = datetime.now(UTC)
        succeeded = sum(
            result.dispatch_status == SyncDispatchStatus.SUCCESS for result in results
        )
        failed = sum(
            result.dispatch_status == SyncDispatchStatus.FAILED for result in results
        )
        already_running = sum(
            result.dispatch_status == SyncDispatchStatus.ALREADY_RUNNING
            for result in results
        )
        attempted = succeeded + failed
        skipped = len(results) - attempted - already_running

        return ExternalSyncBatchSummary(
            mode=mode,
            started_at=started_at,
            finished_at=finished_at,
            total_sources=len(sources),
            attempted=attempted,
            succeeded=succeeded,
            failed=failed,
            already_running=already_running,
            skipped=skipped,
            results=tuple(results),
        )

    def _skip_status(
        self,
        source: ExternalDataSource,
        mode: SyncBatchMode,
        now: datetime,
    ) -> SyncDispatchStatus | None:
        if not source.enabled:
            return SyncDispatchStatus.SKIPPED_DISABLED
        if mode == SyncBatchMode.MANUAL_ALL:
            return None
        if source.sync_mode != SyncMode.AUTOMATIC:
            return SyncDispatchStatus.SKIPPED_MANUAL
        if not is_source_due(
            source,
            now=now,
            failure_retry_hours=self.settings.external_sync_failure_retry_hours,
        ):
            return SyncDispatchStatus.SKIPPED_NOT_DUE
        return None

    def _success_result(
        self,
        source: ExternalDataSource,
        summary: SyncSummary,
    ) -> ExternalSyncDispatchResult:
        return ExternalSyncDispatchResult(
            source_id=source.id,
            source_code=source.code,
            dispatch_status=SyncDispatchStatus.SUCCESS,
            run_id=summary.run_id,
            sync_status=summary.status,
            records_received=summary.records_received,
            records_created=summary.records_created,
            records_updated=summary.records_updated,
            records_unchanged=summary.records_unchanged,
            records_rejected=summary.records_rejected,
            next_due_at=calculate_next_due_at(
                source,
                failure_retry_hours=self.settings.external_sync_failure_retry_hours,
            ),
            error=None,
        )

    def _empty_result(
        self,
        source: ExternalDataSource,
        *,
        dispatch_status: SyncDispatchStatus,
        error: str | None,
        run_id: UUID | None = None,
        sync_status: SyncRunStatus | None = None,
    ) -> ExternalSyncDispatchResult:
        return ExternalSyncDispatchResult(
            source_id=source.id,
            source_code=source.code,
            dispatch_status=dispatch_status,
            run_id=run_id,
            sync_status=sync_status,
            records_received=0,
            records_created=0,
            records_updated=0,
            records_unchanged=0,
            records_rejected=0,
            next_due_at=calculate_next_due_at(
                source,
                failure_retry_hours=self.settings.external_sync_failure_retry_hours,
            ),
            error=error,
        )

    async def _running_runs_by_source(self) -> dict[UUID, UUID]:
        rows = (
            await self.session.execute(
                select(ExternalSyncRun.source_id, ExternalSyncRun.id)
                .where(ExternalSyncRun.status == SyncRunStatus.RUNNING)
                .order_by(ExternalSyncRun.started_at.desc())
            )
        ).all()
        result: dict[UUID, UUID] = {}
        for source_id, run_id in rows:
            result.setdefault(source_id, run_id)
        return result
