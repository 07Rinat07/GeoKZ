from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ConflictStatus, ConflictType, enum_type

if TYPE_CHECKING:
    from app.models.fact import Fact

conflict_facts = Table(
    "conflict_facts",
    Base.metadata,
    Column(
        "conflict_id",
        PGUUID(as_uuid=True),
        ForeignKey("conflict_records.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "fact_id",
        PGUUID(as_uuid=True),
        ForeignKey("facts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ConflictRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conflict_records"

    external_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geological_entities.id", ondelete="CASCADE"),
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    conflict_type: Mapped[ConflictType] = mapped_column(
        enum_type(ConflictType, "conflict_type"),
        nullable=False,
    )
    expert_question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConflictStatus] = mapped_column(
        enum_type(ConflictStatus, "conflict_status"),
        default=ConflictStatus.OPEN,
        nullable=False,
    )
    resolution_fact_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("facts.id", ondelete="SET NULL"),
    )

    facts: Mapped[list["Fact"]] = relationship(secondary=conflict_facts)
