from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.project_info import SupportedLanguage
from app.schemas.coordinates import CoordinateInput, ResolvedCoordinate
from app.schemas.correlation import WellCrossSectionViewResponse
from app.schemas.explorer import IntervalCard, WellCard


class DemoCorrelationWorkflowStage(StrEnum):
    DISCOVERY = "DISCOVERY"
    CROSS_SECTION_READY = "CROSS_SECTION_READY"


class DemoCorrelationWorkflowRequest(BaseModel):
    coordinate: CoordinateInput
    radius_km: float = Field(default=5.0, gt=0, le=50)
    language: SupportedLanguage = "ru"
    limit: int = Field(default=10, ge=2, le=50)
    reference_well_id: UUID | None = None
    well_ids: list[UUID] = Field(default_factory=list, max_length=20)


class DemoCorrelationWellOption(BaseModel):
    distance_m: float
    well: WellCard
    intervals: list[IntervalCard]
    passport_path: str
    synthetic: Literal[True] = True


class DemoCorrelationSelection(BaseModel):
    reference_well_id: UUID
    compared_well_ids: list[UUID]


class DemoCorrelationSelectionContract(BaseModel):
    method: Literal["POST"] = "POST"
    path: Literal["/api/v1/correlation/demo/workflow"] = (
        "/api/v1/correlation/demo/workflow"
    )
    minimum_total_wells: Literal[2] = 2
    maximum_compared_wells: Literal[20] = 20


class DemoCorrelationWorkflowResponse(BaseModel):
    dataset_code: str
    synthetic: Literal[True] = True
    warning: str
    selection_note: str
    stage: DemoCorrelationWorkflowStage
    resolved_coordinate: ResolvedCoordinate
    nearby_demo_wells: list[DemoCorrelationWellOption]
    suggested_reference_well_id: UUID | None
    can_build_cross_section: bool
    selection_contract: DemoCorrelationSelectionContract
    selection: DemoCorrelationSelection | None = None
    cross_section: WellCrossSectionViewResponse | None = None
