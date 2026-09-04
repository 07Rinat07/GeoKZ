from decimal import Decimal
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
