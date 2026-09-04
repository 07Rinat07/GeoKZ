from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.project_info import SupportedLanguage
from app.models.enums import (
    DepthReference,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
)
from app.schemas.correlation import MarkerDifference, ReservoirDifference
from app.schemas.explorer import WellCard


class CrossSectionLayer(StrEnum):
    MARKERS = "markers"
    LITHOLOGY = "lithology"
    RESERVOIRS = "reservoirs"
    FLUIDS = "fluids"


class CrossSectionRequest(BaseModel):
    reference_well_id: UUID
    well_ids: list[UUID] = Field(min_length=1, max_length=20)
    language: SupportedLanguage = "ru"
    depth_reference: DepthReference = DepthReference.TVDSS
    layers: list[CrossSectionLayer] = Field(
        default_factory=lambda: list(CrossSectionLayer),
        min_length=1,
    )

    @field_validator("depth_reference")
    @classmethod
    def reject_unknown_depth_reference(cls, value: DepthReference) -> DepthReference:
        if value == DepthReference.UNKNOWN:
            raise ValueError("Для разреза необходимо выбрать MD, TVD или TVDSS")
        return value

    @field_validator("layers")
    @classmethod
    def deduplicate_layers(
        cls, value: list[CrossSectionLayer]
    ) -> list[CrossSectionLayer]:
        return list(dict.fromkeys(value))


class CrossSectionAxis(BaseModel):
    depth_reference: DepthReference
    min_depth_m: Decimal | None
    max_depth_m: Decimal | None
    depth_increases_downward: bool = True


class CrossSectionMarker(BaseModel):
    marker_id: UUID
    marker_code: str
    marker_type: str
    display_name: str
    plot_depth_m: Decimal | None
    source_depth_m: Decimal
    source_depth_reference: DepthReference
    confidence_percent: Decimal | None
    verification_status: VerificationStatus
    plottable: bool


class CrossSectionInterval(BaseModel):
    interval_id: UUID
    external_id: str
    local_horizon: str | None
    plot_top_depth_m: Decimal | None
    plot_base_depth_m: Decimal | None
    source_top_depth_m: Decimal
    source_base_depth_m: Decimal
    source_depth_reference: DepthReference
    lithologies: list[str]
    porosity_percent: Decimal | None
    permeability_md: Decimal | None
    net_pay_m: Decimal | None
    fluid_type: FluidType
    hydrocarbon_status: HydrocarbonStatus
    verification_status: VerificationStatus
    plottable: bool


class CrossSectionColumn(BaseModel):
    column_index: int
    well: WellCard
    distance_from_reference_m: float | None
    markers: list[CrossSectionMarker]
    intervals: list[CrossSectionInterval]
    warnings: list[str] = Field(default_factory=list)


class CrossSectionTie(BaseModel):
    marker_code: str
    display_name: str
    from_column_index: int
    to_column_index: int
    from_well_id: UUID
    to_well_id: UUID
    from_depth_m: Decimal
    to_depth_m: Decimal
    confidence_percent: Decimal | None


class CrossSectionResponse(BaseModel):
    language: SupportedLanguage
    reference_well_id: UUID
    depth_reference: DepthReference
    layers: list[CrossSectionLayer]
    axis: CrossSectionAxis
    columns: list[CrossSectionColumn]
    ties: list[CrossSectionTie]
    marker_differences: list[MarkerDifference]
    reservoir_differences: list[ReservoirDifference]
    warnings: list[str] = Field(default_factory=list)
    interpretation_note: str
