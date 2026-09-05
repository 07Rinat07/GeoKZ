from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.core.project_info import SupportedLanguage
from app.models.enums import VocabularyCode

VocabularyInputValue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=300),
]


class VocabularyResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


class VocabularyCatalogItem(BaseModel):
    vocabulary: VocabularyCode
    display_name: str
    language: SupportedLanguage
    active_terms: int


class VocabularyTermRead(BaseModel):
    id: UUID
    vocabulary: VocabularyCode
    code: str
    display_name: str
    name_ru: str
    name_kk: str
    name_en: str
    aliases: list[str]
    description: str | None
    source_reference: str
    metadata_payload: dict
    is_active: bool


class VocabularyResolveRequest(BaseModel):
    values: list[VocabularyInputValue] = Field(min_length=1, max_length=100)


class VocabularyResolutionRead(BaseModel):
    input_value: str
    status: VocabularyResolutionStatus
    term: VocabularyTermRead | None = None


class VocabularyResolveResponse(BaseModel):
    vocabulary: VocabularyCode
    language: SupportedLanguage
    results: list[VocabularyResolutionRead]
