"""Add authentication, append-only audit log and master-data revisions.

Revision ID: 20260905_0010
Revises: 20260905_0009
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260905_0010"
down_revision: str | None = "20260905_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_ROLE = sa.Enum(
    "expert",
    "editor",
    "admin",
    name="user_role",
    native_enum=False,
    create_constraint=True,
)
AUDIT_ACTOR_ROLE = sa.Enum(
    "expert",
    "editor",
    "admin",
    name="audit_actor_role",
    native_enum=False,
    create_constraint=True,
)
REVISION_ACTOR_ROLE = sa.Enum(
    "expert",
    "editor",
    "admin",
    name="revision_actor_role",
    native_enum=False,
    create_constraint=True,
)
AUDIT_ACTION = sa.Enum(
    "CREATE",
    "UPDATE",
    "REVIEW",
    "LOGIN",
    "LOGOUT",
    "INSTALL",
    name="audit_action",
    native_enum=False,
    create_constraint=True,
)
REVISION_ACTION = sa.Enum(
    "CREATE",
    "UPDATE",
    "REVIEW",
    "LOGIN",
    "LOGOUT",
    "INSTALL",
    name="revision_action",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("role", USER_ROLE, nullable=False),
        sa.Column("password_hash", sa.String(length=300), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_user_accounts_username"), "user_accounts", ["username"], unique=True)
    op.create_index(op.f("ix_user_accounts_role"), "user_accounts", ["role"], unique=False)
    op.create_index(op.f("ix_user_accounts_is_active"), "user_accounts", ["is_active"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_auth_sessions_token_hash"), "auth_sessions", ["token_hash"], unique=True)
    op.create_index(op.f("ix_auth_sessions_expires_at"), "auth_sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_auth_sessions_revoked_at"), "auth_sessions", ["revoked_at"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("actor_username", sa.String(length=120), nullable=False),
        sa.Column("actor_role", AUDIT_ACTOR_ROLE, nullable=False),
        sa.Column("action", AUDIT_ACTION, nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=200), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_occurred_at"), "audit_logs", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_username"), "audit_logs", ["actor_username"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)

    op.create_table(
        "master_data_revisions",
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("action", REVISION_ACTION, nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("actor_username", sa.String(length=120), nullable=False),
        sa.Column("actor_role", REVISION_ACTOR_ROLE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_type",
            "resource_id",
            "revision_number",
            name="uq_master_data_revision_number",
        ),
    )
    op.create_index(
        op.f("ix_master_data_revisions_resource_type"),
        "master_data_revisions",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_master_data_revisions_resource_id"),
        "master_data_revisions",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_master_data_revisions_actor_user_id"),
        "master_data_revisions",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_master_data_revisions_created_at"),
        "master_data_revisions",
        ["created_at"],
        unique=False,
    )

    op.execute(
        """
        CREATE FUNCTION geokz_reject_immutable_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only and cannot be updated or deleted', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION geokz_reject_immutable_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_master_data_revisions_append_only
        BEFORE UPDATE OR DELETE ON master_data_revisions
        FOR EACH ROW EXECUTE FUNCTION geokz_reject_immutable_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_master_data_revisions_append_only ON master_data_revisions")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS geokz_reject_immutable_mutation()")

    op.drop_index(op.f("ix_master_data_revisions_created_at"), table_name="master_data_revisions")
    op.drop_index(op.f("ix_master_data_revisions_actor_user_id"), table_name="master_data_revisions")
    op.drop_index(op.f("ix_master_data_revisions_resource_id"), table_name="master_data_revisions")
    op.drop_index(op.f("ix_master_data_revisions_resource_type"), table_name="master_data_revisions")
    op.drop_table("master_data_revisions")

    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_username"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_occurred_at"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_auth_sessions_revoked_at"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_expires_at"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_token_hash"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_table("auth_sessions")

    op.drop_index(op.f("ix_user_accounts_is_active"), table_name="user_accounts")
    op.drop_index(op.f("ix_user_accounts_role"), table_name="user_accounts")
    op.drop_index(op.f("ix_user_accounts_username"), table_name="user_accounts")
    op.drop_table("user_accounts")
