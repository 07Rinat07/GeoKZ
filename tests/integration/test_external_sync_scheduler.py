import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.external_sync import ExternalSyncService
from app.integrations.contracts import ExternalRecordEnvelope
from app.integrations.errors import ExternalSyncAlreadyRunningError
from app.integrations.types import SyncMode, SyncRunStatus
from app.models.integration import ExternalDataSource, ExternalSyncRun

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for integration tests",
)


class FakeConnector:
    def __init__(self, source_code: str) -> None:
        self._source_code = source_code

    @property
    def source_code(self) -> str:
        return self._source_code

    async def check_availability(self) -> bool:
        return True

    async def get_dataset_version(self) -> str | None:
        return "test-v1"

    async def fetch_records(self, *, updated_since=None, cursor=None):
        del updated_since, cursor
        yield ExternalRecordEnvelope(
            external_id="record-1",
            record_type="scheduler_test",
            raw_payload={"name": "scheduler test"},
            language="en",
        )


def _source(code: str) -> ExternalDataSource:
    return ExternalDataSource(
        code=code,
        name_ru=code,
        name_kk=code,
        name_en=code,
        base_url="https://example.invalid",
        enabled=True,
        sync_mode=SyncMode.AUTOMATIC,
        sync_interval_hours=168,
        source_config={},
    )


@pytest.mark.asyncio
async def test_active_run_blocks_second_sync() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = _source("it-scheduler-active-lock")
            session.add(source)
            await session.flush()
            active = ExternalSyncRun(
                source_id=source.id,
                status=SyncRunStatus.RUNNING,
                started_at=datetime.now(UTC),
            )
            session.add(active)
            await session.commit()
            active_id = active.id
            source_id = source.id
            source_code = source.code

            with pytest.raises(ExternalSyncAlreadyRunningError) as error_info:
                await ExternalSyncService(
                    session,
                    running_timeout_hours=6,
                ).sync(source_id, FakeConnector(source_code))

            assert error_info.value.run_id == active_id
            await session.refresh(active)
            assert active.status == SyncRunStatus.RUNNING
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_stale_run_is_failed_before_new_sync_succeeds() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            source = _source("it-scheduler-stale-recovery")
            session.add(source)
            await session.flush()
            stale = ExternalSyncRun(
                source_id=source.id,
                status=SyncRunStatus.RUNNING,
                started_at=datetime.now(UTC) - timedelta(hours=7),
            )
            session.add(stale)
            await session.commit()

            summary = await ExternalSyncService(
                session,
                running_timeout_hours=6,
            ).sync(source.id, FakeConnector(source.code))

            await session.refresh(stale)
            await session.refresh(source)
            assert stale.status == SyncRunStatus.FAILED
            assert stale.finished_at is not None
            assert "stale" in (stale.error_message or "")
            assert summary.status == SyncRunStatus.SUCCESS
            assert summary.records_received == 1
            assert summary.records_created == 1
            assert source.last_success_at is not None
            assert source.dataset_version == "test-v1"
    finally:
        await engine.dispose()
