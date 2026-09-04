from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.project_info import (
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    PROJECT_INFO,
    PROJECT_NAME,
    PROJECT_VERSION,
    SUPPORTED_LANGUAGES,
    SupportedLanguage,
)

router = APIRouter()


class AboutResponse(BaseModel):
    application: str
    version: str
    language: SupportedLanguage
    title: str
    description: str
    author: str
    email: str
    supported_languages: tuple[SupportedLanguage, ...]


@router.get("", response_model=AboutResponse)
async def get_about(
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
) -> AboutResponse:
    localized = PROJECT_INFO[lang]
    return AboutResponse(
        application=PROJECT_NAME,
        version=PROJECT_VERSION,
        language=lang,
        title=localized["title"],
        description=localized["description"],
        author=AUTHOR_NAME,
        email=AUTHOR_EMAIL,
        supported_languages=SUPPORTED_LANGUAGES,
    )
