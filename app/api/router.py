from fastapi import APIRouter

from app.api.routes import about, entities, facts, health, sources
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(
    about.router,
    prefix=f"{settings.api_prefix}/about",
    tags=["about"],
)
api_router.include_router(
    sources.router,
    prefix=f"{settings.api_prefix}/sources",
    tags=["sources"],
)
api_router.include_router(
    entities.router,
    prefix=f"{settings.api_prefix}/entities",
    tags=["entities"],
)
api_router.include_router(
    facts.router,
    prefix=f"{settings.api_prefix}/facts",
    tags=["facts"],
)
