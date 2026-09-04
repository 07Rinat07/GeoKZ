import pytest

from app.schemas.coordinates import (
    GeographicCoordinateInput,
    ProjectedAxisOrder,
    ProjectedCoordinateInput,
)


def test_projected_coordinates_accept_comma_decimal_separator() -> None:
    coordinate = ProjectedCoordinateInput(
        x="5085125,325",
        y="711157,665",
        crs="EPSG:32639",
        axis_order=ProjectedAxisOrder.X_NORTHING_Y_EASTING,
    )

    assert coordinate.x == pytest.approx(5085125.325)
    assert coordinate.y == pytest.approx(711157.665)


def test_projected_coordinates_accept_dot_decimal_separator() -> None:
    coordinate = ProjectedCoordinateInput(
        x="5085125.325",
        y="711157.665",
        crs="EPSG:32639",
        axis_order=ProjectedAxisOrder.X_NORTHING_Y_EASTING,
    )

    assert coordinate.x == pytest.approx(5085125.325)
    assert coordinate.y == pytest.approx(711157.665)


def test_coordinates_accept_spaces_from_copied_text() -> None:
    coordinate = ProjectedCoordinateInput(
        x="5 085 125,325",
        y="711 157.665",
        crs="EPSG:32639",
        axis_order=ProjectedAxisOrder.X_NORTHING_Y_EASTING,
    )

    assert coordinate.x == pytest.approx(5085125.325)
    assert coordinate.y == pytest.approx(711157.665)


def test_geographic_coordinates_accept_both_decimal_separators() -> None:
    coordinate = GeographicCoordinateInput(
        latitude="43,652341",
        longitude="51.168420",
    )

    assert coordinate.latitude == pytest.approx(43.652341)
    assert coordinate.longitude == pytest.approx(51.168420)
