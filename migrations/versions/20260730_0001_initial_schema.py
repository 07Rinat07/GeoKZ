"""Initial GeoKZ evidence schema.

Revision ID: 20260730_0001
Revises: None
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def enum(*values: str, name: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    op.create_table(
        "sources",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("organization", sa.String(500)),
        sa.Column("publication_year", sa.SmallInteger()),
        sa.Column("survey_year_start", sa.SmallInteger()),
        sa.Column("survey_year_end", sa.SmallInteger()),
        sa.Column(
            "document_type",
            enum("report", "book", "article", "map", "registry", "thesis", "project", "dataset", "web_page", name="source_document_type"),
            nullable=False,
        ),
        sa.Column("language", sa.String(16), server_default="ru", nullable=False),
        sa.Column("territories", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("objects", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("inventory_number", sa.String(200)),
        sa.Column("doi", sa.String(300)),
        sa.Column("url", sa.Text()),
        sa.Column("access_date", sa.Date()),
        sa.Column(
            "access_level",
            enum("FULL", "ABSTRACT_ONLY", "METADATA_ONLY", "PAID", "RESTRICTED", "LOCAL", name="source_access_level"),
            server_default="LOCAL",
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer()),
        sa.Column("map_scale", sa.String(100)),
        sa.Column("coordinate_system", sa.String(300)),
        sa.Column("license", sa.String(500)),
        sa.Column("sha256", sa.String(64)),
        sa.Column("reliability_level", enum("A", "B", "C", "D", "E", name="source_reliability_level"), nullable=False),
        sa.Column("notes", sa.Text()),
        *timestamps(),
        sa.CheckConstraint("publication_year IS NULL OR publication_year BETWEEN 1500 AND 2100", name="ck_sources_publication_year"),
        sa.CheckConstraint("survey_year_start IS NULL OR survey_year_start BETWEEN 1500 AND 2100", name="ck_sources_survey_year_start"),
        sa.CheckConstraint("survey_year_end IS NULL OR survey_year_end BETWEEN 1500 AND 2100", name="ck_sources_survey_year_end"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_sources_external_id", "sources", ["external_id"])
    op.create_index("ix_sources_doi", "sources", ["doi"])
    op.create_index("ix_sources_sha256", "sources", ["sha256"])
    op.execute("CREATE INDEX ix_sources_title_trgm ON sources USING gin (title gin_trgm_ops)")

    op.create_table(
        "documents",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(1000), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("media_type", sa.String(200), nullable=False),
        sa.Column("size_bytes", sa.BigInteger()),
        sa.Column("page_count", sa.Integer()),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "extraction_status",
            enum("PENDING", "EXTRACTED", "NEEDS_REVIEW", "FAILED", name="document_extraction_status"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("extraction_error", sa.Text()),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("sha256"),
    )
    op.create_index("ix_documents_source_id", "documents", ["source_id"])
    op.create_index("ix_documents_sha256", "documents", ["sha256"])

    op.create_table(
        "document_pages",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("normalized_text", sa.Text()),
        sa.Column(
            "extraction_method",
            enum("pdf_text", "ocr", "docx", "csv", "manual", "import", name="page_extraction_method"),
            nullable=False,
        ),
        sa.Column("ocr_confidence", sa.Float()),
        sa.Column("requires_manual_review", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("page_image_path", sa.Text()),
        *timestamps(),
        sa.CheckConstraint("page_number > 0", name="ck_document_pages_positive_number"),
        sa.CheckConstraint("ocr_confidence IS NULL OR (ocr_confidence >= 0 AND ocr_confidence <= 1)", name="ck_document_pages_ocr_confidence"),
        sa.UniqueConstraint("document_id", "page_number", name="uq_document_pages_number"),
    )
    op.create_index("ix_document_pages_document_id", "document_pages", ["document_id"])
    op.execute("CREATE INDEX ix_document_pages_fts_ru ON document_pages USING gin (to_tsvector('russian', coalesce(normalized_text, '')))")

    op.create_table(
        "administrative_regions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("administrative_regions.id", ondelete="SET NULL")),
        sa.Column("level", sa.String(64), nullable=False),
        sa.Column("name_ru", sa.String(500), nullable=False),
        sa.Column("name_kk", sa.String(500)),
        sa.Column("name_en", sa.String(500)),
        sa.Column("notes", sa.Text()),
        sa.Column("geometry", geoalchemy2.types.Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False)),
        *timestamps(),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_administrative_regions_external_id", "administrative_regions", ["external_id"])
    op.create_index("ix_administrative_regions_parent_id", "administrative_regions", ["parent_id"])
    op.create_index("ix_administrative_regions_level", "administrative_regions", ["level"])
    op.execute("CREATE INDEX ix_administrative_regions_name_trgm ON administrative_regions USING gin (name_ru gin_trgm_ops)")
    op.create_index("ix_administrative_regions_geometry", "administrative_regions", ["geometry"], postgresql_using="gist")

    op.create_table(
        "geological_entities",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("object_type", sa.String(80), nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="SET NULL")),
        sa.Column("name_ru", sa.String(500), nullable=False),
        sa.Column("name_kk", sa.String(500)),
        sa.Column("name_en", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("geological_context", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("geometry", geoalchemy2.types.Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False)),
        sa.Column("geometry_status", enum("EXACT", "APPROXIMATE", "DIGITIZED", "UNKNOWN", name="entity_geometry_status"), server_default="UNKNOWN", nullable=False),
        sa.Column("geometry_source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("verification_status", enum("DRAFT", "REVIEWED", "VERIFIED", "CONFLICT", "REJECTED", "OBSOLETE", name="entity_verification_status"), server_default="DRAFT", nullable=False),
        *timestamps(),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_geological_entities_external_id", "geological_entities", ["external_id"])
    op.create_index("ix_geological_entities_object_type", "geological_entities", ["object_type"])
    op.create_index("ix_geological_entities_parent_id", "geological_entities", ["parent_id"])
    op.execute("CREATE INDEX ix_geological_entities_name_trgm ON geological_entities USING gin (name_ru gin_trgm_ops)")
    op.create_index("ix_geological_entities_geometry", "geological_entities", ["geometry"], postgresql_using="gist")

    op.create_table(
        "geological_entity_administrative_regions",
        sa.Column("entity_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("administrative_region_id", UUID, sa.ForeignKey("administrative_regions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relation_type", sa.String(64), server_default="located_in", nullable=False),
    )

    op.create_table(
        "entity_names",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("entity_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("language", sa.String(16), server_default="ru", nullable=False),
        sa.Column("name_type", enum("canonical", "historical", "transliteration", "abbreviation", "ocr_variant", "synonym", name="entity_name_type"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("is_preferred", sa.Boolean(), server_default=sa.false(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("entity_id", "name", "language", name="uq_entity_names_value"),
    )
    op.create_index("ix_entity_names_entity_id", "entity_names", ["entity_id"])
    op.execute("CREATE INDEX ix_entity_names_name_trgm ON entity_names USING gin (name gin_trgm_ops)")

    op.create_table(
        "facts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("primary_source_id", UUID, sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("entity_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="SET NULL")),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("category", enum("tectonics", "stratigraphy", "lithology", "hydrocarbon", "water", "well", "map", "history", "geography", "environment", name="fact_category"), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("normalized_statement", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("figure_number", sa.String(100)),
        sa.Column("table_number", sa.String(100)),
        sa.Column("section_title", sa.String(1000)),
        sa.Column("methods", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("fact_kind", enum("OBSERVATION", "MEASUREMENT", "INTERPRETATION", "FORECAST", "HISTORICAL", name="fact_kind"), nullable=False),
        sa.Column("valid_time_start", sa.SmallInteger()),
        sa.Column("valid_time_end", sa.SmallInteger()),
        sa.Column("confidence", enum("A", "B", "C", "D", "E", "CONFLICT", "UNKNOWN", name="fact_confidence"), server_default="UNKNOWN", nullable=False),
        sa.Column("needs_human_review", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("review_reason", sa.Text()),
        sa.Column("verification_status", enum("DRAFT", "REVIEWED", "VERIFIED", "CONFLICT", "REJECTED", "OBSOLETE", name="fact_verification_status"), server_default="DRAFT", nullable=False),
        sa.Column("related_fact_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        *timestamps(),
        sa.CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_facts_page_number"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_facts_external_id", "facts", ["external_id"])
    op.create_index("ix_facts_primary_source_id", "facts", ["primary_source_id"])
    op.create_index("ix_facts_entity_id", "facts", ["entity_id"])
    op.create_index("ix_facts_category", "facts", ["category"])
    op.execute("CREATE INDEX ix_facts_statement_fts_ru ON facts USING gin (to_tsvector('russian', normalized_statement))")

    op.create_table(
        "fact_evidences",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("fact_id", UUID, sa.ForeignKey("facts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", UUID, sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("page_from", sa.Integer()),
        sa.Column("page_to", sa.Integer()),
        sa.Column("quote_text", sa.Text()),
        sa.Column("evidence_role", enum("supports", "contradicts", "mentions", "contextualizes", name="evidence_role"), server_default="supports", nullable=False),
        sa.Column("extraction_method", enum("pdf_text", "ocr", "docx", "csv", "manual", "import", name="evidence_extraction_method"), nullable=False),
        sa.Column("reviewer_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("reviewer_comment", sa.Text()),
        *timestamps(),
        sa.CheckConstraint("page_from IS NULL OR page_from > 0", name="ck_evidence_page_from"),
        sa.CheckConstraint("page_to IS NULL OR page_to > 0", name="ck_evidence_page_to"),
        sa.CheckConstraint("page_from IS NULL OR page_to IS NULL OR page_to >= page_from", name="ck_evidence_page_order"),
    )
    op.create_index("ix_fact_evidences_fact_id", "fact_evidences", ["fact_id"])
    op.create_index("ix_fact_evidences_source_id", "fact_evidences", ["source_id"])

    op.create_table(
        "wells",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("entity_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("aliases", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("object_entity_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="SET NULL")),
        sa.Column("well_type", enum("structural", "exploration", "appraisal", "production", "hydrogeological", "other", name="well_type"), nullable=False),
        sa.Column("spud_date", sa.Date()),
        sa.Column("completion_date", sa.Date()),
        sa.Column("total_depth_m", sa.Numeric(10, 2)),
        sa.Column("location", geoalchemy2.types.Geometry(geometry_type="POINT", srid=4326, spatial_index=False)),
        sa.Column("coordinate_system_original", sa.String(300)),
        sa.Column("coordinate_accuracy", enum("EXACT", "APPROXIMATE", "DIGITIZED", "UNKNOWN", name="well_coordinate_accuracy"), server_default="UNKNOWN", nullable=False),
        sa.Column("operator", sa.String(500)),
        sa.Column("bottomhole_unit", sa.String(300)),
        sa.Column("core_available", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("logs_available", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("tests_available", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("status", sa.String(200)),
        sa.Column("source_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("verification_status", enum("DRAFT", "REVIEWED", "VERIFIED", "CONFLICT", "REJECTED", "OBSOLETE", name="well_verification_status"), server_default="DRAFT", nullable=False),
        *timestamps(),
        sa.CheckConstraint("total_depth_m IS NULL OR total_depth_m >= 0", name="ck_wells_depth"),
        sa.UniqueConstraint("external_id"),
        sa.UniqueConstraint("entity_id"),
    )
    op.create_index("ix_wells_external_id", "wells", ["external_id"])
    op.create_index("ix_wells_entity_id", "wells", ["entity_id"])
    op.create_index("ix_wells_object_entity_id", "wells", ["object_entity_id"])
    op.execute("CREATE INDEX ix_wells_name_trgm ON wells USING gin (name gin_trgm_ops)")
    op.create_index("ix_wells_location", "wells", ["location"], postgresql_using="gist")

    op.create_table(
        "well_intervals",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(240), nullable=False),
        sa.Column("well_id", UUID, sa.ForeignKey("wells.id", ondelete="CASCADE"), nullable=False),
        sa.Column("top_depth_m", sa.Numeric(10, 2), nullable=False),
        sa.Column("base_depth_m", sa.Numeric(10, 2), nullable=False),
        sa.Column("depth_reference", enum("MD", "TVD", "TVDSS", "UNKNOWN", name="interval_depth_reference"), server_default="UNKNOWN", nullable=False),
        sa.Column("stratigraphic_unit_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="SET NULL")),
        sa.Column("local_horizon", sa.String(300)),
        sa.Column("lithologies", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("porosity_percent", sa.Numeric(7, 3)),
        sa.Column("permeability_md", sa.Numeric(14, 4)),
        sa.Column("net_pay_m", sa.Numeric(10, 2)),
        sa.Column("fluid_type", enum("OIL", "GAS", "CONDENSATE", "WATER", "BRINE", "MIXED", "UNKNOWN", name="interval_fluid_type"), server_default="UNKNOWN", nullable=False),
        sa.Column("hydrocarbon_status", enum("COMMERCIAL_FIELD", "DISCOVERED_ACCUMULATION", "TESTED_FLOW", "LOG_INTERPRETATION", "OIL_SHOW", "GAS_SHOW", "BITUMEN_SHOW", "PROSPECTIVE", "PREDICTED", "NEGATIVE", "UNKNOWN", name="interval_hydrocarbon_status"), server_default="UNKNOWN", nullable=False),
        sa.Column("test_result", sa.Text()),
        sa.Column("flow_rate", sa.Numeric(16, 4)),
        sa.Column("flow_rate_unit", sa.String(100)),
        sa.Column("pressure_mpa", sa.Numeric(10, 4)),
        sa.Column("temperature_c", sa.Numeric(10, 3)),
        sa.Column("source_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("verification_status", enum("DRAFT", "REVIEWED", "VERIFIED", "CONFLICT", "REJECTED", "OBSOLETE", name="interval_verification_status"), server_default="DRAFT", nullable=False),
        *timestamps(),
        sa.CheckConstraint("top_depth_m >= 0", name="ck_intervals_top_depth"),
        sa.CheckConstraint("base_depth_m >= top_depth_m", name="ck_intervals_depth_order"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_well_intervals_external_id", "well_intervals", ["external_id"])
    op.create_index("ix_well_intervals_well_id", "well_intervals", ["well_id"])
    op.create_index("ix_well_intervals_local_horizon", "well_intervals", ["local_horizon"])

    op.create_table(
        "conflict_records",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("entity_id", UUID, sa.ForeignKey("geological_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("conflict_type", enum("VALUE", "GEOMETRY", "AGE", "STATUS", "TERMINOLOGY", "OTHER", name="conflict_type"), nullable=False),
        sa.Column("expert_question", sa.Text(), nullable=False),
        sa.Column("status", enum("OPEN", "RESOLVED", name="conflict_status"), server_default="OPEN", nullable=False),
        sa.Column("resolution_fact_id", UUID, sa.ForeignKey("facts.id", ondelete="SET NULL")),
        *timestamps(),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_conflict_records_external_id", "conflict_records", ["external_id"])
    op.create_index("ix_conflict_records_entity_id", "conflict_records", ["entity_id"])
    op.create_index("ix_conflict_records_category", "conflict_records", ["category"])

    op.create_table(
        "conflict_facts",
        sa.Column("conflict_id", UUID, sa.ForeignKey("conflict_records.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("fact_id", UUID, sa.ForeignKey("facts.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("conflict_facts")
    op.drop_table("conflict_records")
    op.drop_table("well_intervals")
    op.drop_table("wells")
    op.drop_table("fact_evidences")
    op.drop_table("facts")
    op.drop_table("entity_names")
    op.drop_table("geological_entity_administrative_regions")
    op.drop_table("geological_entities")
    op.drop_table("administrative_regions")
    op.drop_table("document_pages")
    op.drop_table("documents")
    op.drop_table("sources")
