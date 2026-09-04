from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.project_info import SupportedLanguage
from app.models.enums import DepthReference, FluidType, HydrocarbonStatus, VerificationStatus
from app.schemas.explorer import WellCard


class WellCorrelationRequest(BaseModel):
    reference_well_id: UUID
    well_ids: list[UUID] = Field(min_length=1, max_length=20)
    language: SupportedLanguage = "ru"


class CorrelationMarker(BaseModel):
    id: UUID
    marker_code: str
    marker_type: str
    display_name: str
    depth_m: Decimal
    depth_reference: DepthReference
    measured_depth_m: Decimal | None
    true_vertical_depth_m: Decimal | None
    tvdss_m: Decimal | None
    confidence_percent: Decimal | None
    verification_status: VerificationStatus


class CorrelationInterval(BaseModel):
    id: UUID
    external_id: str
    top_depth_m: Decimal
    base_depth_m: Decimal
    depth_reference: DepthReference
    local_horizon: str | None
    lithologies: list[str]
    porosity_percent: Decimal | None
    permeability_md: Decimal | None
    net_pay_m: Decimal | None
    fluid_type: FluidType
    hydrocarbon_status: HydrocarbonStatus
    verification_status: VerificationStatus


class CorrelationWellColumn(BaseModel):
    well: WellCard
    distance_from_reference_m: float | None
    markers: list[CorrelationMarker]
    intervals: list[CorrelationInterval]


class MarkerDifference(BaseModel):
    marker_code: str
    compared_well_id: UUID
    reference_depth_m: Decimal | None
    compared_depth_m: Decimal | None
    depth_reference: DepthReference | None
    delta_m: Decimal | None
    comparable: bool
    reason: str | None = None


class ReservoirDifference(BaseModel):
    horizon: str
    compared_well_id: UUID
    reference_interval_id: UUID
    compared_interval_id: UUID
    depth_reference: DepthReference | None
    reference_thickness_m: Decimal
    compared_thickness_m: Decimal
    thickness_delta_m: Decimal | None
    reference_net_pay_m: Decimal | None
    compared_net_pay_m: Decimal | None
    net_pay_delta_m: Decimal | None
    reference_porosity_percent: Decimal | None
    compared_porosity_percent: Decimal | None
    reference_permeability_md: Decimal | None
    compared_permeability_md: Decimal | None
    reference_lithologies: list[str]
    compared_lithologies: list[str]
    lithology_changed: bool
    reference_fluid_type: FluidType
    compared_fluid_type: FluidType
    fluid_changed: bool
    reference_hydrocarbon_status: HydrocarbonStatus
    compared_hydrocarbon_status: HydrocarbonStatus
    hydrocarbon_status_changed: bool
    comparable_thickness: bool
    reason: str | None = None


class WellCorrelationResponse(BaseModel):
    language: SupportedLanguage
    reference_well_id: UUID
    columns: list[CorrelationWellColumn]
    marker_differences: list[MarkerDifference]
    reservoir_differences: list[ReservoirDifference]
    comparison_note: str


class CrossSectionLineKind(StrEnum):
    MARKER = "MARKER"
    HORIZON = "HORIZON"


class CrossSectionWarningCode(StrEnum):
    DEPTH_REFERENCE_MISMATCH = "DEPTH_REFERENCE_MISMATCH"
    NON_COMPARABLE_MARKERS = "NON_COMPARABLE_MARKERS"
    NON_COMPARABLE_INTERVALS = "NON_COMPARABLE_INTERVALS"
    NO_RENDERABLE_DATA = "NO_RENDERABLE_DATA"
    NO_CORRELATION_LINES = "NO_CORRELATION_LINES"


class CrossSectionDepthAxis(BaseModel):
    depth_reference: DepthReference
    unit: Literal["m"] = "m"
    direction: Literal["DOWN"] = "DOWN"
    min_depth_m: Decimal
    max_depth_m: Decimal
    padding_m: Decimal


class CrossSectionMarkerView(BaseModel):
    marker_id: UUID
    marker_code: str
    display_name: str
    marker_type: str
    depth_m: Decimal | None
    depth_reference: DepthReference
    renderable: bool
    confidence_percent: Decimal | None
    verification_status: VerificationStatus


class CrossSectionIntervalView(BaseModel):
    interval_id: UUID
    external_id: str
    horizon: str | None
    top_depth_m: Decimal | None
    base_depth_m: Decimal | None
    depth_reference: DepthReference
    renderable: bool
    lithologies: list[str]
    fluid_type: FluidType
    hydrocarbon_status: HydrocarbonStatus
    net_pay_m: Decimal | None
    verification_status: VerificationStatus


class CrossSectionWellColumnView(BaseModel):
    column_index: int = Field(ge=0)
    well: WellCard
    is_reference: bool
    distance_from_reference_m: float | None
    markers: list[CrossSectionMarkerView]
    intervals: list[CrossSectionIntervalView]


class CrossSectionCorrelationLine(BaseModel):
    kind: CrossSectionLineKind
    key: str
    depth_reference: DepthReference
    from_column_index: int = Field(ge=0)
    to_column_index: int = Field(ge=0)
    from_well_id: UUID
    to_well_id: UUID
    from_depth_m: Decimal
    to_depth_m: Decimal


class CrossSectionWarning(BaseModel):
    code: CrossSectionWarningCode
    message: str
    well_id: UUID | None = None
    key: str | None = None


class WellCrossSectionViewResponse(BaseModel):
    language: SupportedLanguage
    reference_well_id: UUID
    title: str
    policy_note: str
    depth_axis: CrossSectionDepthAxis
    columns: list[CrossSectionWellColumnView]
    correlation_lines: list[CrossSectionCorrelationLine]
    warnings: list[CrossSectionWarning]
    has_renderable_data: bool
