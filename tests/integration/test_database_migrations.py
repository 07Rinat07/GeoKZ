import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

INTEGRATION_DATABASE_URL = os.getenv("GEOKZ_INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="GEOKZ_INTEGRATION_DATABASE_URL is required for PostgreSQL/PostGIS integration tests",
)


@pytest.mark.asyncio
async def test_alembic_head_and_required_extensions() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
            assert revision == "20260904_0004"

            extensions = set(
                (
                    await connection.execute(
                        text(
                            "SELECT extname FROM pg_extension "
                            "WHERE extname IN ('postgis', 'pg_trgm', 'unaccent')"
                        )
                    )
                ).scalars()
            )
            assert extensions == {"postgis", "pg_trgm", "unaccent"}

            tables = set(
                (
                    await connection.execute(
                        text(
                            "SELECT table_name FROM information_schema.tables "
                            "WHERE table_schema = 'public'"
                        )
                    )
                ).scalars()
            )
            assert {
                "administrative_regions",
                "geological_entities",
                "wells",
                "well_intervals",
                "well_trajectory_points",
                "well_log_runs",
                "well_log_curves",
                "well_tests",
                "core_runs",
                "core_samples",
                "seismic_surveys",
                "seismic_lines",
                "seismic_volumes",
                "well_markers",
                "external_data_sources",
                "external_records",
                "external_sync_runs",
            } <= tables

            postgis_version = await connection.scalar(text("SELECT PostGIS_Version()"))
            assert isinstance(postgis_version, str)
            assert postgis_version
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_postgis_geography_distance_is_in_meters() -> None:
    assert INTEGRATION_DATABASE_URL is not None
    engine = create_async_engine(INTEGRATION_DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            distance_m = await connection.scalar(
                text(
                    "SELECT ST_Distance("
                    "ST_SetSRID(ST_MakePoint(51.168420, 43.652341), 4326)::geography, "
                    "ST_SetSRID(ST_MakePoint(51.180000, 43.652341), 4326)::geography"
                    ")"
                )
            )
            assert distance_m is not None
            assert 800 < float(distance_m) < 1100
    finally:
        await engine.dispose()
