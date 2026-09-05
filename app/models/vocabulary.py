from sqlalchemy import Boolean, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VocabularyCode, enum_type


class ControlledVocabularyTerm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Versionable controlled term used to normalize geological working data.

    Raw/source wording is intentionally kept in domain records. This registry provides
    canonical GeoKZ codes without silently rewriting source evidence.
    """

    __tablename__ = "controlled_vocabulary_terms"
    __table_args__ = (
        UniqueConstraint(
            "vocabulary",
            "code",
            name="uq_controlled_vocabulary_term_code",
        ),
    )

    vocabulary: Mapped[VocabularyCode] = mapped_column(
        enum_type(VocabularyCode, "controlled_vocabulary_code"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    name_ru: Mapped[str] = mapped_column(String(300), nullable=False)
    name_kk: Mapped[str] = mapped_column(String(300), nullable=False)
    name_en: Mapped[str] = mapped_column(String(300), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_payload: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
        index=True,
    )
