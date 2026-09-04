from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import (
    CoordinateAccuracy,
    DepthReference,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
    WellType,
)
from app.schemas.common import ORMModel


class LocalizedName(BaseModel):
    ru: str | None = None
    kk: str | None = None
    en: str | None = None


class WellHeader(BaseModel):
    id: UUID
    external_id: str
    name: str
    aliases: list[str]
    localized_name: LocalizedName
    well_type: WellType
    status: str | None
    operator: str | None
    spud_date: date | None
    completion_date: date | None
    total_depth_m: Decimal | None
    longitude: float | None
    latitude: float | None
    coordinate_system_original: str | None
    coordinate_accuracy: CoordinateAccuracy
    object_entity_id: UUID | None
    verification_status: VerificationStatus


class WellIntervalSummary(ORMModel):
    id: UUID
    external_id: str
    top_depth_m: Decimal
    base_depth_m: Decimal
    depth_reference: DepthReference
    stratigraphic_unit_id: UUID | None
    local_horizon: str | None
    lithologies: list[str]
    porosity_percent: Decimal | None
    permeability_md: Decimal | None
    net_pay_m: Decimal | None
    fluid_type: FluidType
    hydrocarbon_status: HydrocarbonStatus
    test_result: str | None
    flow_rate: Decimal | None
    flow_rate_unit: str | None
    pressure_mpa: Decimal | None
    temperature_c: Decimal | None
    verification_status: VerificationStatus


class WellTrajectoryPointSummary(ORMModel):
    id: UUID
    station_index: int
    measured_depth_m: Decimal
    true_vertical_depth_m: Decimal | None
    tvdss_m: Decimal | None
    inclination_deg: Decimal | None
    azimuth_deg: Decimal | None
    survey_method: str | None
    verification_status: VerificationStatus


class WellLogCurveSummary(ORMModel):
    id: UUID
    log_run_id: UUID
    mnemonic_original: str
    property_kind: str | None
    description: str | None
    unit_original: str | None
    canonical_unit: str | None
    sample_count: int | None
    min_value: Decimal | None
    max_value: Decimal | None


class WellLogRunSummary(ORMModel):
    id: UUID
    external_id: str
    name: str
    acquisition_type: str
    run_number: str | None
    top_depth_m: Decimal
    base_depth_m: Decimal
    depth_reference: DepthReference
    acquisition_at: datetime | None
    service_company: str | None
    tool_name: str | None
    file_format: str | None
    sha256: str | None
    source_id: UUID | None
    document_id: UUID | None
    verification_status: VerificationStatus


class WellTestSummary(ORMModel):
    id: UUID
    external_id: str
    test_type: str
    test_date: date | None
    top_depth_m: Decimal
    base_depth_m: Decimal
    depth_reference: DepthReference
    stratigraphic_unit_id: UUID | None
    pressure_mpa: Decimal | None
    temperature_c: Decimal | None
    oil_rate: Decimal | None
    oil_rate_unit: str | None
    gas_rate: Decimal | None
    gas_rate_unit: str | None
    water_rate: Decimal | None
    water_rate_unit: str | None
    result_text: str | None
    interpretation_text: str | None
    source_id: UUID | None
    verification_status: VerificationStatus


class CoreRunSummary(ORMModel):
    id: UUID
    external_id: str
    top_depth_m: Decimal
    base_depth_m: Decimal
    depth_reference: DepthReference
    recovery_percent: Decimal | None
    description: str | None
    source_id: UUID | None


class CoreSampleSummary(ORMModel):
    id: UUID
    core_run_id: UUID
    sample_code: str | None
    depth_m: Decimal
    sample_type: str | None
    lithologies: list[str]
    porosity_percent: Decimal | None
    permeability_md: Decimal | None
    grain_density_g_cm3: Decimal | None
    measurements: dict
    source_id: UUID | None


class WellPassportResponse(BaseModel):
    well: WellHeader
    intervals: list[WellIntervalSummary]
    trajectory: list[WellTrajectoryPointSummary]
    log_runs: list[WellLogRunSummary]
    log_curves: list[WellLogCurveSummary]
    tests: list[WellTestSummary]
    core_runs: list[CoreRunSummary]
    core_samples: list[CoreSampleSummary]
