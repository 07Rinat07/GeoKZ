from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.core.help_content import get_help_topic, get_help_topics
from app.schemas.help import HelpTopic, HelpTopicListResponse

router = APIRouter()


@router.get("/topics", response_model=HelpTopicListResponse)
async def list_help_topics(
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
) -> HelpTopicListResponse:
    return HelpTopicListResponse(language=lang, topics=get_help_topics(lang))


@router.get("/topics/{code}", response_model=HelpTopic)
async def get_help_topic_by_code(
    code: str,
    lang: Literal["ru", "kk", "en"] = Query(default="ru"),
) -> HelpTopic:
    topic = get_help_topic(code, lang)
    if topic is None:
        raise HTTPException(status_code=404, detail="Help topic not found")
    return topic
