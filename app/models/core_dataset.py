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
