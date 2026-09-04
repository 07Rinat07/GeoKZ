from pyproj import CRS

from app.core.crs_catalog import get_crs_presets


def test_crs_catalog_contains_wgs84_and_kazakhstan_utm_zones() -> None:
    response = get_crs_presets("ru")
    epsg_codes = {preset.epsg for preset in response.presets}

    assert 4326 in epsg_codes
    assert {32600 + zone for zone in range(38, 46)} <= epsg_codes

    for preset in response.presets:
        crs = CRS.from_epsg(preset.epsg)
        if preset.coordinate_type == "geographic":
            assert crs.is_geographic
        else:
            assert crs.is_projected


def test_crs_catalog_is_localized() -> None:
    ru = get_crs_presets("ru")
    kk = get_crs_presets("kk")
    en = get_crs_presets("en")

    assert ru.presets[0].display_name != kk.presets[0].display_name
    assert en.presets[0].display_name != ru.presets[0].display_name
    assert ru.warning
    assert kk.warning
    assert en.warning
