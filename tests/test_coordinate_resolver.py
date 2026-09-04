import pytest

from app.application.coordinates import CoordinateResolver
from app.application.errors import CoordinateResolutionError
from app.schemas.coordinates import (
    GeographicCoordinateInput,
    ProjectedAxisOrder,
    ProjectedCoordinateInput,
)


def test_geographic_wgs84_is_preserved() -> None:
    result = CoordinateResolver().resolve(
        GeographicCoordinateInput(
            latitude="43,652341",
            longitude="51.168420",
        )
    )
    assert result.latitude == pytest.approx(43.652341)
    assert result.longitude == pytest.approx(51.168420)
    assert result.source_crs == "EPSG:4326"


def test_projected_utm_resolves_with_explicit_axis_order() -> None:
    resolver = CoordinateResolver()
    projected = ProjectedCoordinateInput(
        x="711157,665",
        y="4851250.325",
        crs="EPSG:32639",
        axis_order=ProjectedAxisOrder.X_EASTING_Y_NORTHING,
    )
    result = resolver.resolve(projected)

    assert 40 < result.latitude < 50
    assert 48 < result.longitude < 54
    assert result.source_x == pytest.approx(711157.665)
    assert result.source_y == pytest.approx(4851250.325)


def test_projected_northing_easting_axis_order_is_supported() -> None:
    resolver = CoordinateResolver()
    easting_first = resolver.resolve(
        ProjectedCoordinateInput(
            x=711157.665,
            y=4851250.325,
            crs="EPSG:32639",
            axis_order=ProjectedAxisOrder.X_EASTING_Y_NORTHING,
        )
    )
    northing_first = resolver.resolve(
        ProjectedCoordinateInput(
            x=4851250.325,
            y=711157.665,
            crs="EPSG:32639",
            axis_order=ProjectedAxisOrder.X_NORTHING_Y_EASTING,
        )
    )
    assert northing_first.latitude == pytest.approx(easting_first.latitude)
    assert northing_first.longitude == pytest.approx(easting_first.longitude)


def test_projected_type_rejects_geographic_crs() -> None:
    with pytest.raises(CoordinateResolutionError):
        CoordinateResolver().resolve(
            ProjectedCoordinateInput(
                x=51.168420,
                y=43.652341,
                crs="EPSG:4326",
                axis_order=ProjectedAxisOrder.X_EASTING_Y_NORTHING,
            )
        )
