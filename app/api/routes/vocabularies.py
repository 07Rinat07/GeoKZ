from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.vocabularies import ControlledVocabularyService
from app.core.database import get_session
from app.core.project_info import SupportedLanguage
from app.models.enums import VocabularyCode
from app.schemas.vocabulary import (
    VocabularyCatalogItem,
    VocabularyResolveRequest,
    VocabularyResolveResponse,
    VocabularyTermRead,
)

router = APIRouter()


@router.get("", response_model=list[VocabularyCatalogItem])
async def list_vocabularies(
    lang: SupportedLanguage = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> list[VocabularyCatalogItem]:
    return await ControlledVocabularyService(session).catalog(lang)


@router.get("/{vocabulary}/terms", response_model=list[VocabularyTermRead])
async def list_vocabulary_terms(
    vocabulary: VocabularyCode,
    lang: SupportedLanguage = Query(default="ru"),
    include_inactive: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> list[VocabularyTermRead]:
    return await ControlledVocabularyService(session).list_terms(
        vocabulary=vocabulary,
        language=lang,
        include_inactive=include_inactive,
    )


@router.post("/{vocabulary}/resolve", response_model=VocabularyResolveResponse)
async def resolve_vocabulary_values(
    vocabulary: VocabularyCode,
    payload: VocabularyResolveRequest,
    lang: SupportedLanguage = Query(default="ru"),
    session: AsyncSession = Depends(get_session),
) -> VocabularyResolveResponse:
    return await ControlledVocabularyService(session).resolve(
        vocabulary=vocabulary,
        values=payload.values,
        language=lang,
    )
