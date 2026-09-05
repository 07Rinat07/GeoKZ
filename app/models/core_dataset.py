from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CoreDatasetState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Installed state of one independently versioned GeoKZ baseline dataset."""

    __tablename__ = "core_dataset_states"

    dataset_code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    dataset_version: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source_path: Mapped[str | None] = mapped_column(Text)
    file_checksums: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )
    item_counts: Mapped[dict[str, int]] = mapped_column(
        JSONB,
        default=dict,
        server_default="{}",
        nullable=False,
    )

    # One-step rollback metadata. The previous bundle remains immutable in the update cache
    # (or points to the bundled manifest) and can be reactivated only when identity sets match.
    previous_dataset_version: Mapped[str | None] = mapped_column(String(120))
    previous_schema_version: Mapped[int | None] = mapped_column(Integer)
    previous_manifest_sha256: Mapped[str | None] = mapped_column(String(64))
    previous_installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    previous_source_path: Mapped[str | None] = mapped_column(Text)
    previous_file_checksums: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    previous_item_counts: Mapped[dict[str, int] | None] = mapped_column(JSONB)

    # Provenance of the most recent signed online activation.
    last_update_source_url: Mapped[str | None] = mapped_column(Text)
    last_update_bundle_sha256: Mapped[str | None] = mapped_column(String(64))
    last_update_key_id: Mapped[str | None] = mapped_column(String(120))
