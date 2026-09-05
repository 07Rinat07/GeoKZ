from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.core_dataset_manifest import CoreDatasetManifestError, load_core_dataset_manifest
from app.core.database import get_session
from app.core.project_info import PROJECT_VERSION
from app.models.core_dataset import CoreDatasetState

router = APIRouter()


class SystemVersionsResponse(BaseModel):
    application_version: str
    database_schema_version: str | None
    bundled_core_dataset_version: str | None
    bundled_core_dataset_schema_version: int | None
    installed_core_dataset_version: str | None
    installed_core_dataset_schema_version: int | None
    installed_core_dataset_at: datetime | None


@router.get("/versions", response_model=SystemVersionsResponse)
async def get_system_versions(
    session: AsyncSession = Depends(get_session),
) -> SystemVersionsResponse:
    database_schema_version = await session.scalar(text("SELECT version_num FROM alembic_version"))
    installed = await session.scalar(
        select(CoreDatasetState).where(CoreDatasetState.dataset_code == "geokz-core")
    )
    try:
        bundled = load_core_dataset_manifest()
    except CoreDatasetManifestError:
        bundled = None

    return SystemVersionsResponse(
        application_version=PROJECT_VERSION,
        database_schema_version=(
            str(database_schema_version) if database_schema_version is not None else None
        ),
        bundled_core_dataset_version=(bundled.dataset_version if bundled is not None else None),
        bundled_core_dataset_schema_version=(bundled.schema_version if bundled is not None else None),
        installed_core_dataset_version=(installed.dataset_version if installed is not None else None),
        installed_core_dataset_schema_version=(installed.schema_version if installed is not None else None),
        installed_core_dataset_at=(installed.installed_at if installed is not None else None),
    )
