# GeoKZ — external synchronization scheduler (EN)

## Purpose

GeoKZ synchronizes permitted external data sources outside the main FastAPI request-processing loop. The periodic scheduler runs as a dedicated process/container and does not create a background loop inside every API worker. This prevents duplicate synchronization when the API is scaled horizontally.

Core flow:

```text
GeoKZ API / PySide6
        |
        +--> POST /api/v1/integrations/sync-all       # manual Update All
        |
        +--> GET  /api/v1/integrations/scheduler/status

Dedicated scheduler process
        |
        +--> ExternalSyncCoordinator.sync_due()
        |
        +--> source reservation in PostgreSQL
        |
        +--> connector -> RAW/staging -> checksum/diff
```

## Run modes

### Manual Update All

```text
POST /api/v1/integrations/sync-all
```

The command attempts to synchronize every enabled source for which GeoKZ has a connector factory. Sources with `enabled=false` are skipped. If one source is already being synchronized, the batch does not fail: that source returns `ALREADY_RUNNING` while the remaining sources continue.

### Scheduled run for due sources only

```text
POST /api/v1/integrations/scheduler/run-due
```

This endpoint executes the same due-source algorithm as the dedicated scheduler process and is intended for diagnostics or an explicit manual run. Production deployments should not invoke it independently from multiple cron jobs or FastAPI workers.

The scheduler considers only sources with `sync_mode=AUTOMATIC` and applies each source's own `sync_interval_hours`.

### Scheduler status

```text
GET /api/v1/integrations/scheduler/status
```

The response exposes:

- `poll_seconds` — how often the dedicated scheduler process checks due state;
- `failure_retry_hours` — retry delay after the latest error;
- `running_timeout_hours` — stale `RUNNING` threshold;
- `sources[]` — per-source state;
- `next_due_at` and `due`;
- `running_run_id` when a sync is currently active;
- latest successful synchronization and latest error information.

## Parallel-run protection

Before a new `ExternalSyncRun(status=RUNNING)` is created, GeoKZ briefly locks the relevant `external_data_sources` row with PostgreSQL `SELECT ... FOR UPDATE`.

The critical section contains only run reservation:

1. lock the source row;
2. look for a current `RUNNING` run;
3. convert stale `RUNNING` rows to `FAILED`;
4. create the new `RUNNING` row;
5. commit and release the row lock.

The external HTTP transfer is performed after the row lock has been released. A slow provider therefore does not hold a long database lock against status reads or other sources.

If a second synchronization request arrives while a current run exists, GeoKZ raises `ExternalSyncAlreadyRunningError`. The single-source REST endpoint maps this condition to HTTP `409`.

## Stale RUNNING recovery

A crashed process may leave a run in `RUNNING`. GeoKZ does not treat such a row as a permanent lock.

The threshold is configured with:

```env
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

During the next reservation, `RUNNING` rows whose `started_at` is older than the threshold are changed to `FAILED` with a diagnostic `error_message`. A new run can then start.

## Due and retry policy

A new `AUTOMATIC` source with no synchronization history is immediately `due=true`.

After a success:

```text
next_due_at = last_success_at + sync_interval_hours
```

When the latest error is newer than the latest success:

```text
next_due_at = last_error_at + min(sync_interval_hours, failure_retry_hours)
```

A retry therefore never occurs less frequently than the source's normal synchronization interval.

`MANUAL` and disabled sources have no scheduled `next_due_at`.

## Batch status

Both `sync-all` and `run-due` return a batch summary and one result per source.

Stable `dispatch_status` values:

- `SUCCESS` — synchronization completed successfully;
- `FAILED` — connector, configuration or provider failure;
- `ALREADY_RUNNING` — another run currently owns the source;
- `SKIPPED_NOT_DUE` — scheduled batch, but the source is not due yet;
- `SKIPPED_DISABLED` — the source is disabled;
- `SKIPPED_MANUAL` — the source does not participate in scheduled due runs;
- `SKIPPED_UNSUPPORTED` — the source is registered but no connector factory exists yet.

A failure for one source never cancels the remaining batch.

## Docker Compose

`docker compose up --build` starts three processes:

```text
geokz-db
geokz-api
geokz-external-sync-scheduler
```

The scheduler waits for a healthy API and then runs:

```text
python -m scripts.external_sync_scheduler
```

One-shot diagnostic run:

```text
python -m scripts.external_sync_scheduler --once
```

## Settings

`.env`:

```env
GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS=300
GEOKZ_EXTERNAL_SYNC_FAILURE_RETRY_HOURS=6
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

`poll_seconds` does not modify a source's `sync_interval_hours`; it controls only how often the worker checks whether `next_due_at` has arrived.

## API keys and offline behavior

The scheduler does not make external APIs a mandatory GeoKZ runtime dependency. If `GEOKZ_EGOV_API_KEY` is absent, the local database, search, passports and review workflows continue to work. An eGov synchronization attempt is recorded as a per-source error while the scheduler process remains alive.

API keys must never be sent in GeoKZ REST payloads, stored in UI state, committed to Git, or exposed in URLs. They are read only from the configured runtime environment.

## Responsibility boundary

The scheduler is responsible only for safely acquiring RAW/staging records and preserving synchronization history. It does not verify geological facts and does not publish master-data changes.

After synchronization, normalization -> matching -> human review remain separate steps. Verified GeoKZ facts are never overwritten automatically by the scheduler.
