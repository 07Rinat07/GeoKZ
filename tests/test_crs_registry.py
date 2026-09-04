import pytest

from app.application.crs_registry import validate_crs_definition
from app.application.errors import CrsDefinitionValidationError
from app.schemas.crs import CrsDefinitionKind


def test_epsg_projected_definition_is_normalized_and_validated() -> None:
    result = validate_crs_definition(
        CrsDefinitionKind.EPSG,
        "32639",
    )

    assert result.definition == "EPSG:32639"
    assert "PROJCRS" in result.canonical_wkt
    assert result.authority_name == "EPSG"
    assert result.authority_code == "32639"


def test_geographic_crs_is_rejected_for_organization_xy_registry() -> None:
    with pytest.raises(CrsDefinitionValidationError):
        validate_crs_definition(
            CrsDefinitionKind.EPSG,
            "EPSG:4326",
        )


def test_explicit_proj_definition_is_supported() -> None:
    result = validate_crs_definition(
        CrsDefinitionKind.PROJ,
        "+proj=utm +zone=39 +datum=WGS84 +units=m +no_defs",
    )

    assert result.definition.startswith("+proj=utm")
    assert "PROJCRS" in result.canonical_wkt


def test_proj_definition_requires_explicit_proj_parameter() -> None:
    with pytest.raises(CrsDefinitionValidationError):
        validate_crs_definition(
            CrsDefinitionKind.PROJ,
            "EPSG:32639",
        )
