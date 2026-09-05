from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.project_info import SupportedLanguage
from app.models.enums import VocabularyCode
from app.models.vocabulary import ControlledVocabularyTerm
from app.schemas.vocabulary import (
    VocabularyCatalogItem,
    VocabularyResolutionRead,
    VocabularyResolutionStatus,
    VocabularyResolveResponse,
    VocabularyTermRead,
)

_VOCABULARY_NAMES: dict[VocabularyCode, dict[SupportedLanguage, str]] = {
    VocabularyCode.LITHOLOGY: {
        "ru": "Литология",
        "kk": "Литология",
        "en": "Lithology",
    },
    VocabularyCode.MARKER_TYPE: {
        "ru": "Типы корреляционных реперов",
        "kk": "Корреляциялық репер түрлері",
        "en": "Correlation marker types",
    },
    VocabularyCode.PROPERTY_KIND: {
        "ru": "Виды измеряемых свойств",
        "kk": "Өлшенетін қасиет түрлері",
        "en": "Property kinds",
    },
    VocabularyCode.UNIT: {
        "ru": "Единицы измерения",
        "kk": "Өлшем бірліктері",
        "en": "Units of measure",
    },
}


def normalize_vocabulary_value(value: str) -> str:
    """Normalize matching text without changing the persisted source wording."""

    return " ".join(value.casefold().split())


def _display_name(term: ControlledVocabularyTerm, language: SupportedLanguage) -> str:
    return {
        "ru": term.name_ru,
        "kk": term.name_kk,
        "en": term.name_en,
    }[language]


def _term_read(
    term: ControlledVocabularyTerm,
    language: SupportedLanguage,
) -> VocabularyTermRead:
    return VocabularyTermRead(
        id=term.id,
        vocabulary=term.vocabulary,
        code=term.code,
        display_name=_display_name(term, language),
        name_ru=term.name_ru,
        name_kk=term.name_kk,
        name_en=term.name_en,
        aliases=term.aliases,
        description=term.description,
        source_reference=term.source_reference,
        metadata_payload=term.metadata_payload,
        is_active=term.is_active,
    )


@dataclass(slots=True)
class ControlledVocabularyService:
    session: AsyncSession

    async def catalog(
        self,
        language: SupportedLanguage,
    ) -> list[VocabularyCatalogItem]:
        result: list[VocabularyCatalogItem] = []
        for vocabulary in VocabularyCode:
            active_terms = await self.session.scalar(
                select(func.count())
                .select_from(ControlledVocabularyTerm)
                .where(
                    ControlledVocabularyTerm.vocabulary == vocabulary,
                    ControlledVocabularyTerm.is_active.is_(True),
                )
            )
            result.append(
                VocabularyCatalogItem(
                    vocabulary=vocabulary,
                    display_name=_VOCABULARY_NAMES[vocabulary][language],
                    language=language,
                    active_terms=int(active_terms or 0),
                )
            )
        return result

    async def list_terms(
        self,
        *,
        vocabulary: VocabularyCode,
        language: SupportedLanguage,
        include_inactive: bool = False,
    ) -> list[VocabularyTermRead]:
        statement = select(ControlledVocabularyTerm).where(
            ControlledVocabularyTerm.vocabulary == vocabulary
        )
        if not include_inactive:
            statement = statement.where(ControlledVocabularyTerm.is_active.is_(True))
        statement = statement.order_by(ControlledVocabularyTerm.code)
        terms = list(await self.session.scalars(statement))
        return [_term_read(term, language) for term in terms]

    async def resolve(
        self,
        *,
        vocabulary: VocabularyCode,
        values: list[str],
        language: SupportedLanguage,
    ) -> VocabularyResolveResponse:
        terms = list(
            await self.session.scalars(
                select(ControlledVocabularyTerm)
                .where(
                    ControlledVocabularyTerm.vocabulary == vocabulary,
                    ControlledVocabularyTerm.is_active.is_(True),
                )
                .order_by(ControlledVocabularyTerm.code)
            )
        )

        lookup: dict[str, list[ControlledVocabularyTerm]] = {}
        for term in terms:
            candidates = [
                term.code,
                term.name_ru,
                term.name_kk,
                term.name_en,
                *term.aliases,
            ]
            for candidate in candidates:
                key = normalize_vocabulary_value(candidate)
                bucket = lookup.setdefault(key, [])
                if term not in bucket:
                    bucket.append(term)

        results: list[VocabularyResolutionRead] = []
        for value in values:
            matches = lookup.get(normalize_vocabulary_value(value), [])
            if len(matches) == 1:
                results.append(
                    VocabularyResolutionRead(
                        input_value=value,
                        status=VocabularyResolutionStatus.RESOLVED,
                        term=_term_read(matches[0], language),
                    )
                )
            elif len(matches) > 1:
                results.append(
                    VocabularyResolutionRead(
                        input_value=value,
                        status=VocabularyResolutionStatus.AMBIGUOUS,
                    )
                )
            else:
                results.append(
                    VocabularyResolutionRead(
                        input_value=value,
                        status=VocabularyResolutionStatus.UNRESOLVED,
                    )
                )

        return VocabularyResolveResponse(
            vocabulary=vocabulary,
            language=language,
            results=results,
        )
