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
            assert revision == "20260905_0008"

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
                "organization_crs_definitions",
                "controlled_vocabulary_terms",
            } <= tables

            vocabulary_constraint = await connection.scalar(
                text(
                    "SELECT pg_get_constraintdef(c.oid) "
                    "FROM pg_constraint c "
                    "JOIN pg_class t ON t.oid = c.conrelid "
                    "WHERE t.relname = 'controlled_vocabulary_terms' "
                    "AND c.conname = 'ck_controlled_vocabulary_code'"
                )
            )
            assert vocabulary_constraint is not None
            assert "lithology" in vocabulary_constraint
            assert "marker_type" in vocabulary_constraint

            columns = set(
                (
                    await connection.execute(
                        text(
                            "SELECT table_name, column_name FROM information_schema.columns "
                            "WHERE table_schema = 'public' AND table_name IN "
                            "('well_intervals', 'well_markers', 'well_log_curves', "
                            "'well_tests', 'core_samples', 'external_records')"
                        )
                    )
                ).tuples()
            )
            assert {
                ("well_intervals", "lithology_codes"),
                ("well_intervals", "flow_rate_unit_code"),
                ("well_markers", "marker_type_code"),
                ("well_log_curves", "property_kind_code"),
                ("well_log_curves", "unit_code"),
                ("well_tests", "oil_rate_unit_code"),
                ("well_tests", "gas_rate_unit_code"),
                ("well_tests", "water_rate_unit_code"),
                ("core_samples", "lithology_codes"),
                ("external_records", "reviewed_by"),
                ("external_records", "reviewed_at"),
                ("external_records", "review_comment"),
            } <= columns

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
