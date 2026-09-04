from enum import StrEnum

from pydantic import BaseModel

from app.core.project_info import SupportedLanguage


class HelpLevel(StrEnum):
    HINT = "hint"
    CONTEXT = "context"
    WIZARD = "wizard"
    WARNING = "warning"


class HelpTopic(BaseModel):
    code: str
    title: str
    short_hint: str
    details: str
    level: HelpLevel
    language: SupportedLanguage
    related_codes: list[str] = []


class HelpTopicListResponse(BaseModel):
    language: SupportedLanguage
    topics: list[HelpTopic]
