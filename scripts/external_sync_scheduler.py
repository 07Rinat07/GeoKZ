import argparse
import asyncio
import logging

from app.application.external_sync_coordinator import ExternalSyncCoordinator
from app.application.kazakhstan_open_data import KazakhstanOpenDataService
from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, engine

LOGGER = logging.getLogger("geokz.external_sync_scheduler")


async def run_scheduler_iteration() -> None:
    settings = get_settings()
    async with AsyncSessionFactory() as session:
        # Built-in source registration is local-only and idempotent. It keeps a fresh
        # installation ready for scheduled sync without requiring a manual API call.
        await KazakhstanOpenDataService(session, settings).register_all()
        summary = await ExternalSyncCoordinator(session, settings).sync_due()

    LOGGER.info(
        "External sync iteration: total=%s attempted=%s succeeded=%s failed=%s "
        "already_running=%s skipped=%s",
        summary.total_sources,
        summary.attempted,
        summary.succeeded,
        summary.failed,
        summary.already_running,
        summary.skipped,
    )
    for result in summary.results:
        if result.error:
            LOGGER.warning(
                "External source %s: %s: %s",
                result.source_code,
                result.dispatch_status,
                result.error,
            )


async def run_scheduler(*, once: bool) -> None:
    settings = get_settings()
    while True:
        try:
            await run_scheduler_iteration()
        except Exception:
            # A scheduler process must remain alive when one iteration fails because of
            # a transient database/provider problem. Per-source provider failures are
            # already captured by ExternalSyncCoordinator and normally do not reach here.
            LOGGER.exception("External sync scheduler iteration failed")

        if once:
            return
        await asyncio.sleep(settings.external_scheduler_poll_seconds)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the dedicated GeoKZ external-data synchronization scheduler."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Check and synchronize due sources once, then exit.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = _parse_args()
    try:
        asyncio.run(run_scheduler(once=args.once))
    finally:
        # asyncio.run owns the event loop; dispose through a short fresh loop afterwards.
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
