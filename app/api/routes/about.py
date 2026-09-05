from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.core_dataset_manifest import (
    CORE_DATASET_SCHEMA_VERSION,
    CoreDatasetManifestError,
    load_core_dataset_manifest,
)
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
    core_dataset_version: str | None
    core_dataset_schema_version: int
    language: SupportedLanguage
    title: str
    description: str
    author: str
    email: str
    supported_languages: tuple[SupportedLanguage, ...]


def _bundled_core_dataset_version() -> str | None:
    try:
        return load_core_dataset_manifest().dataset_version
    except CoreDatasetManifestError:
        return None


@router.get("", response_model=AboutResponse)
async def get_about(
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
) -> AboutResponse:
    localized = PROJECT_INFO[lang]
    return AboutResponse(
        application=PROJECT_NAME,
        version=PROJECT_VERSION,
        core_dataset_version=_bundled_core_dataset_version(),
        core_dataset_schema_version=CORE_DATASET_SCHEMA_VERSION,
        language=lang,
        title=localized["title"],
        description=localized["description"],
        author=AUTHOR_NAME,
        email=AUTHOR_EMAIL,
        supported_languages=SUPPORTED_LANGUAGES,
    )
