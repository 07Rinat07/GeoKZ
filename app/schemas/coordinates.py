from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class ProjectedAxisOrder(StrEnum):
    """Как исходная система подписывает плоские координаты X/Y."""

    X_EASTING_Y_NORTHING = "x_easting_y_northing"
    X_NORTHING_Y_EASTING = "x_northing_y_easting"


def _parse_decimal(value: float | int | str) -> float:
    if isinstance(value, str):
        normalized = value.strip().replace(" ", "").replace(",", ".")
        return float(normalized)
    return float(value)


class GeographicCoordinateInput(BaseModel):
    type: Literal["geographic"] = "geographic"
    latitude: float = Field(
        description=(
            "Широта в градусах. Рекомендуемый формат: 43.652341. "
            "Также принимается 43,652341."
        ),
        examples=[43.652341],
    )
    longitude: float = Field(
        description=(
            "Долгота в градусах. Рекомендуемый формат: 51.168420. "
            "Также принимается 51,168420."
        ),
        examples=[51.168420],
    )
    crs: str = Field(
        default="EPSG:4326",
        description="Система координат. Для обычной широты/долготы используется EPSG:4326.",
        examples=["EPSG:4326"],
    )

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def parse_decimal(cls, value: float | int | str) -> float:
        return _parse_decimal(value)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("Широта должна быть в диапазоне от -90 до 90 градусов")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if not -180 <= value <= 180:
            raise ValueError("Долгота должна быть в диапазоне от -180 до 180 градусов")
        return value


class ProjectedCoordinateInput(BaseModel):
    type: Literal["projected"] = "projected"
    x: float = Field(
        description=(
            "Проекционная координата X. Рекомендуемый формат: 5085125.325. "
            "Также принимается 5085125,325 и значения с пробелами при копировании."
        ),
        examples=[5085125.325],
    )
    y: float = Field(
        description=(
            "Проекционная координата Y. Рекомендуемый формат: 711157.665. "
            "Также принимается 711157,665 и значения с пробелами при копировании."
        ),
        examples=[711157.665],
    )
    crs: str = Field(
        min_length=3,
        max_length=1000,
        description=(
            "Исходная система координат, например EPSG-код. Для больших X/Y в метрах "
            "систему координат нельзя определять только по значениям — её нужно выбрать "
            "или подтвердить по исходным материалам."
        ),
        examples=["EPSG:32639"],
    )
    axis_order: ProjectedAxisOrder = Field(
        description=(
            "Порядок осей исходных данных. В производственных материалах X нередко означает "
            "Northing, а Y — Easting."
        )
    )

    @field_validator("x", "y", mode="before")
    @classmethod
    def parse_decimal(cls, value: float | int | str) -> float:
        return _parse_decimal(value)


CoordinateInput = Annotated[
    GeographicCoordinateInput | ProjectedCoordinateInput,
    Field(discriminator="type"),
]


class ResolvedCoordinate(BaseModel):
    latitude: float
    longitude: float
    target_crs: str = "EPSG:4326"
    source_crs: str
    source_x: float | None = None
    source_y: float | None = None
    axis_order: ProjectedAxisOrder | None = None
