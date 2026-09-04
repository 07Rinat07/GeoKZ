"""Add external data synchronization staging schema.

Revision ID: 20260904_0002
Revises: 20260730_0001
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260904_0002"
down_revision: str | None = "20260730_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def enum(*values: str, name: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "external_data_sources",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name_ru", sa.String(500), nullable=False),
        sa.Column("name_kk", sa.String(500), nullable=False),
        sa.Column("name_en", sa.String(500), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "sync_mode",
            enum("MANUAL", "AUTOMATIC", name="external_source_sync_mode"),
            server_default="MANUAL",
            nullable=False,
        ),
        sa.Column("sync_interval_hours", sa.Integer(), server_default="168", nullable=False),
        sa.Column("license_name", sa.String(500)),
        sa.Column("license_url", sa.Text()),
        sa.Column("terms_url", sa.Text()),
        sa.Column("dataset_version", sa.String(300)),
        sa.Column("cursor", sa.Text()),
        sa.Column("etag", sa.String(1000)),
        sa.Column("last_modified", sa.String(500)),
        sa.Column("last_sync_started_at", sa.DateTime(timezone=True)),
        sa.Column("last_sync_completed_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_error_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("source_config", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
        sa.CheckConstraint("sync_interval_hours > 0", name="ck_external_sources_sync_interval"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_external_data_sources_code", "external_data_sources", ["code"])

    op.create_table(
        "external_records",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("external_data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(500), nullable=False),
        sa.Column("record_type", sa.String(100), nullable=False),
        sa.Column("language", sa.String(16)),
        sa.Column("raw_payload", JSONB, nullable=False),
        sa.Column("normalized_payload", JSONB),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "status",
            enum(
                "STAGED",
                "UNCHANGED",
                "CHANGED",
                "REVIEW_REQUIRED",
                "ACCEPTED",
                "REJECTED",
                name="external_record_status",
            ),
            server_default="STAGED",
            nullable=False,
        ),
        sa.Column("is_deleted_upstream", sa.Boolean(), server_default=sa.false(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint(
            "source_id",
            "record_type",
            "external_id",
            name="uq_external_records_identity",
        ),
    )
    op.create_index("ix_external_records_source_id", "external_records", ["source_id"])
    op.create_index("ix_external_records_external_id", "external_records", ["external_id"])
    op.create_index("ix_external_records_record_type", "external_records", ["record_type"])
    op.create_index("ix_external_records_language", "external_records", ["language"])
    op.create_index("ix_external_records_checksum", "external_records", ["checksum"])
    op.create_index("ix_external_records_status", "external_records", ["status"])

    op.create_table(
        "external_sync_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "source_id",
            UUID,
            sa.ForeignKey("external_data_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            enum("RUNNING", "SUCCESS", "PARTIAL", "FAILED", name="external_sync_run_status"),
            server_default="RUNNING",
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("records_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_unchanged", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("checkpoint", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_external_sync_runs_source_id", "external_sync_runs", ["source_id"])
    op.create_index("ix_external_sync_runs_status", "external_sync_runs", ["status"])

    op.create_table(
        "external_entity_links",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "external_record_id",
            UUID,
            sa.ForeignKey("external_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "geological_entity_id",
            UUID,
            sa.ForeignKey("geological_entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "match_method",
            enum(
                "EXACT_ID",
                "EXACT_NAME",
                "ALIAS",
                "SPATIAL",
                "FUZZY",
                "MANUAL",
                name="external_entity_match_method",
            ),
            nullable=False,
        ),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column(
            "status",
            enum(
                "AUTO_MATCHED",
                "REVIEW_REQUIRED",
                "VERIFIED",
                "REJECTED",
                name="external_entity_link_status",
            ),
            server_default="REVIEW_REQUIRED",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(300)),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("review_comment", sa.Text()),
        *timestamps(),
        sa.CheckConstraint(
            "match_confidence >= 0 AND match_confidence <= 1",
            name="ck_external_entity_links_confidence",
        ),
        sa.UniqueConstraint(
            "external_record_id",
            "geological_entity_id",
            name="uq_external_entity_links_pair",
        ),
    )
    op.create_index(
        "ix_external_entity_links_external_record_id",
        "external_entity_links",
        ["external_record_id"],
    )
    op.create_index(
        "ix_external_entity_links_geological_entity_id",
        "external_entity_links",
        ["geological_entity_id"],
    )
    op.create_index("ix_external_entity_links_status", "external_entity_links", ["status"])


def downgrade() -> None:
    op.drop_table("external_entity_links")
    op.drop_table("external_sync_runs")
    op.drop_table("external_records")
    op.drop_table("external_data_sources")
