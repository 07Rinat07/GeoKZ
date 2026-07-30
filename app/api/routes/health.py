from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "service": "geokz-api"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    result = await session.execute(
        text("SELECT current_database(), current_setting('server_version'), PostGIS_Version()")
    )
    database, postgresql_version, postgis_version = result.one()
    return {
        "status": "ready",
        "database": database,
        "postgresql": postgresql_version,
        "postgis": postgis_version,
    }
