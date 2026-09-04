from datetime import UTC, datetime, timedelta

from app.application.external_sync_coordinator import (
    calculate_next_due_at,
    is_source_due,
)
from app.integrations.types import SyncMode
from app.models.integration import ExternalDataSource


def _source(
    *,
    enabled: bool = True,
    sync_mode: SyncMode = SyncMode.AUTOMATIC,
    interval_hours: int = 168,
    last_success_at: datetime | None = None,
    last_sync_completed_at: datetime | None = None,
    last_error_at: datetime | None = None,
) -> ExternalDataSource:
    return ExternalDataSource(
        code="test-scheduler-source",
        name_ru="Тестовый источник",
        name_kk="Тест дереккөзі",
        name_en="Test source",
        base_url="https://example.invalid",
        enabled=enabled,
        sync_mode=sync_mode,
        sync_interval_hours=interval_hours,
        source_config={},
        last_success_at=last_success_at,
        last_sync_completed_at=last_sync_completed_at,
        last_error_at=last_error_at,
    )


def test_new_automatic_source_is_due_immediately() -> None:
    source = _source()
    now = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)

    next_due_at = calculate_next_due_at(source, failure_retry_hours=6)

    assert next_due_at is None
    assert is_source_due(source, now=now, failure_retry_hours=6) is True


def test_successful_source_uses_configured_interval() -> None:
    last_success = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    source = _source(interval_hours=168, last_success_at=last_success)

    assert calculate_next_due_at(source, failure_retry_hours=6) == (
        last_success + timedelta(hours=168)
    )
    assert (
        is_source_due(
            source,
            now=last_success + timedelta(hours=167),
            failure_retry_hours=6,
        )
        is False
    )
    assert (
        is_source_due(
            source,
            now=last_success + timedelta(hours=168),
            failure_retry_hours=6,
        )
        is True
    )


def test_latest_failure_uses_bounded_retry_interval() -> None:
    last_success = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    last_error = datetime(2026, 9, 4, 10, 0, tzinfo=UTC)
    source = _source(
        interval_hours=168,
        last_success_at=last_success,
        last_error_at=last_error,
    )

    assert calculate_next_due_at(source, failure_retry_hours=6) == (
        last_error + timedelta(hours=6)
    )


def test_retry_never_exceeds_short_source_interval() -> None:
    last_error = datetime(2026, 9, 4, 10, 0, tzinfo=UTC)
    source = _source(interval_hours=2, last_error_at=last_error)

    assert calculate_next_due_at(source, failure_retry_hours=6) == (
        last_error + timedelta(hours=2)
    )


def test_disabled_and_manual_sources_are_not_scheduled() -> None:
    now = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)

    disabled = _source(enabled=False)
    manual = _source(sync_mode=SyncMode.MANUAL)

    assert calculate_next_due_at(disabled, failure_retry_hours=6) is None
    assert calculate_next_due_at(manual, failure_retry_hours=6) is None
    assert is_source_due(disabled, now=now, failure_retry_hours=6) is False
    assert is_source_due(manual, now=now, failure_retry_hours=6) is False
