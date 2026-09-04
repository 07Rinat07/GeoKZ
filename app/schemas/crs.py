from pydantic import BaseModel

from app.core.project_info import SupportedLanguage
from app.schemas.coordinates import ProjectedAxisOrder


class CrsPreset(BaseModel):
    code: str
    epsg: int
    coordinate_type: str
    display_name: str
    longitude_range: str | None = None
    default_axis_order: ProjectedAxisOrder | None = None
    requires_source_confirmation: bool = True


class CrsPresetListResponse(BaseModel):
    language: SupportedLanguage
    presets: list[CrsPreset]
    warning: str
