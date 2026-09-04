from decimal import Decimal
from uuid import UUID

from app.application.correlation_view import build_cross_section_view
from app.models.enums import (
    DepthReference,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
    WellType,
)
from app.schemas.correlation import (
    CorrelationInterval,
    CorrelationMarker,
    CorrelationWellColumn,
    CrossSectionLineKind,
    CrossSectionWarningCode,
    MarkerDifference,
    ReservoirDifference,
    WellCorrelationResponse,
)
from app.schemas.explorer import WellCard

REFERENCE_WELL_ID = UUID("00000000-0000-0000-0000-000000000101")
COMPARED_WELL_ID = UUID("00000000-0000-0000-0000-000000000102")
REFERENCE_MARKER_ID = UUID("00000000-0000-0000-0000-000000000201")
COMPARED_MARKER_ID = UUID("00000000-0000-0000-0000-000000000202")
MD_ONLY_MARKER_ID = UUID("00000000-0000-0000-0000-000000000203")
REFERENCE_INTERVAL_ID = UUID("00000000-0000-0000-0000-000000000301")
COMPARED_INTERVAL_ID = UUID("00000000-0000-0000-0000-000000000302")


def _well(well_id: UUID, name: str) -> WellCard:
    return WellCard(
        id=well_id,
        external_id=f"test-{name.casefold()}",
        name=name,
        well_type=WellType.EXPLORATION,
        status=None,
        total_depth_m=Decimal("3200"),
        longitude=None,
        latitude=None,
        object_entity_id=None,
        verification_status=VerificationStatus.VERIFIED,
    )


def _marker(
    marker_id: UUID,
    *,
    depth: str,
    reference: DepthReference,
    code: str = "R1",
) -> CorrelationMarker:
    value = Decimal(depth)
    return CorrelationMarker(
        id=marker_id,
        marker_code=code,
        marker_type="stratigraphic",
        display_name=f"Marker {code}",
        depth_m=value,
        depth_reference=reference,
        measured_depth_m=value if reference == DepthReference.MD else None,
        true_vertical_depth_m=value if reference == DepthReference.TVD else None,
        tvdss_m=value if reference == DepthReference.TVDSS else None,
        confidence_percent=Decimal("95"),
        verification_status=VerificationStatus.VERIFIED,
    )


def _interval(
    interval_id: UUID,
    *,
    external_id: str,
    top: str,
    base: str,
) -> CorrelationInterval:
    return CorrelationInterval(
        id=interval_id,
        external_id=external_id,
        top_depth_m=Decimal(top),
        base_depth_m=Decimal(base),
        depth_reference=DepthReference.TVDSS,
        local_horizon="J-II",
        lithologies=["sandstone"],
        porosity_percent=Decimal("16"),
        permeability_md=Decimal("100"),
        net_pay_m=Decimal("15"),
        fluid_type=FluidType.OIL,
        hydrocarbon_status=HydrocarbonStatus.TESTED_FLOW,
        verification_status=VerificationStatus.VERIFIED,
    )


def _correlation() -> WellCorrelationResponse:
    reference_interval = _interval(
        REFERENCE_INTERVAL_ID,
        external_id="ref-j2",
        top="2450",
        base="2478",
    )
    compared_interval = _interval(
        COMPARED_INTERVAL_ID,
        external_id="cmp-j2",
        top="2471",
        base="2492",
    )
    return WellCorrelationResponse(
        language="en",
        reference_well_id=REFERENCE_WELL_ID,
        columns=[
            CorrelationWellColumn(
                well=_well(REFERENCE_WELL_ID, "A-1"),
                distance_from_reference_m=0.0,
                markers=[
                    _marker(
                        REFERENCE_MARKER_ID,
                        depth="2451.6",
                        reference=DepthReference.TVDSS,
                    )
                ],
                intervals=[reference_interval],
            ),
            CorrelationWellColumn(
                well=_well(COMPARED_WELL_ID, "B-1"),
                distance_from_reference_m=930.0,
                markers=[
                    _marker(
                        COMPARED_MARKER_ID,
                        depth="2470",
                        reference=DepthReference.TVDSS,
                    ),
                    _marker(
                        MD_ONLY_MARKER_ID,
                        depth="2600",
                        reference=DepthReference.MD,
                        code="MD-ONLY",
                    ),
                ],
                intervals=[compared_interval],
            ),
        ],
        marker_differences=[
            MarkerDifference(
                marker_code="R1",
                compared_well_id=COMPARED_WELL_ID,
                reference_depth_m=Decimal("2451.6"),
                compared_depth_m=Decimal("2470"),
                depth_reference=DepthReference.TVDSS,
                delta_m=Decimal("18.4"),
                comparable=True,
            )
        ],
        reservoir_differences=[
            ReservoirDifference(
                horizon="J-II",
                compared_well_id=COMPARED_WELL_ID,
                reference_interval_id=REFERENCE_INTERVAL_ID,
                compared_interval_id=COMPARED_INTERVAL_ID,
                depth_reference=DepthReference.TVDSS,
                reference_thickness_m=Decimal("28"),
                compared_thickness_m=Decimal("21"),
                thickness_delta_m=Decimal("-7"),
                reference_net_pay_m=Decimal("15"),
                compared_net_pay_m=Decimal("15"),
                net_pay_delta_m=Decimal("0"),
                reference_porosity_percent=Decimal("16"),
                compared_porosity_percent=Decimal("16"),
                reference_permeability_md=Decimal("100"),
                compared_permeability_md=Decimal("100"),
                reference_lithologies=["sandstone"],
                compared_lithologies=["sandstone"],
                lithology_changed=False,
                reference_fluid_type=FluidType.OIL,
                compared_fluid_type=FluidType.OIL,
                fluid_changed=False,
                reference_hydrocarbon_status=HydrocarbonStatus.TESTED_FLOW,
                compared_hydrocarbon_status=HydrocarbonStatus.TESTED_FLOW,
                hydrocarbon_status_changed=False,
                comparable_thickness=True,
            )
        ],
        comparison_note="test",
    )


def test_cross_section_prefers_tvdss_and_builds_marker_and_horizon_lines() -> None:
    view = build_cross_section_view(_correlation())

    assert view.depth_axis.depth_reference == DepthReference.TVDSS
    assert view.depth_axis.direction == "DOWN"
    assert view.has_renderable_data is True
    assert [column.column_index for column in view.columns] == [0, 1]
    assert view.columns[0].is_reference is True
    assert view.columns[1].is_reference is False

    assert [line.kind for line in view.correlation_lines] == [
        CrossSectionLineKind.MARKER,
        CrossSectionLineKind.HORIZON,
    ]
    marker_line = view.correlation_lines[0]
    assert marker_line.key == "R1"
    assert marker_line.from_depth_m == Decimal("2451.6")
    assert marker_line.to_depth_m == Decimal("2470")

    horizon_line = view.correlation_lines[1]
    assert horizon_line.key == "J-II"
    assert horizon_line.from_depth_m == Decimal("2464")
    assert horizon_line.to_depth_m == Decimal("2481.5")


def test_cross_section_marks_data_from_other_depth_reference_non_renderable() -> None:
    view = build_cross_section_view(_correlation())

    compared = view.columns[1]
    md_only = next(
        marker for marker in compared.markers if marker.marker_code == "MD-ONLY"
    )
    assert md_only.renderable is False
    assert md_only.depth_m is None
    assert CrossSectionWarningCode.DEPTH_REFERENCE_MISMATCH in {
        warning.code for warning in view.warnings
    }
