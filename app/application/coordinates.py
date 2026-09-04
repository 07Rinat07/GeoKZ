from dataclasses import dataclass

from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError, ProjError

from app.application.errors import CoordinateResolutionError
from app.schemas.coordinates import (
    CoordinateInput,
    GeographicCoordinateInput,
    ProjectedAxisOrder,
    ProjectedCoordinateInput,
    ResolvedCoordinate,
)

_WGS84 = CRS.from_epsg(4326)


@dataclass(frozen=True, slots=True)
class CoordinateResolver:
    """Преобразует пользовательские координаты в рабочую точку WGS84.

    Исходные X/Y и CRS не теряются. Для projected-координат порядок осей
    задаётся явно, потому что производственное обозначение X/Y не всегда
    совпадает с GIS-порядком easting/northing.
    """

    def resolve(self, coordinate: CoordinateInput) -> ResolvedCoordinate:
        if isinstance(coordinate, GeographicCoordinateInput):
            return self._resolve_geographic(coordinate)
        return self._resolve_projected(coordinate)

    def _resolve_geographic(
        self,
        coordinate: GeographicCoordinateInput,
    ) -> ResolvedCoordinate:
        source_crs = self._parse_crs(coordinate.crs)
        if not source_crs.is_geographic:
            raise CoordinateResolutionError(
                "Для типа geographic требуется географическая система координат. "
                "Для метрических X/Y используйте type=projected."
            )

        try:
            transformer = Transformer.from_crs(source_crs, _WGS84, always_xy=True)
            longitude, latitude = transformer.transform(
                coordinate.longitude,
                coordinate.latitude,
            )
        except ProjError as error:
            raise CoordinateResolutionError(
                f"Не удалось преобразовать географические координаты из {coordinate.crs}."
            ) from error

        self._validate_wgs84(latitude=latitude, longitude=longitude)
        return ResolvedCoordinate(
            latitude=latitude,
            longitude=longitude,
            source_crs=source_crs.to_string(),
        )

    def _resolve_projected(
        self,
        coordinate: ProjectedCoordinateInput,
    ) -> ResolvedCoordinate:
        if coordinate.crs is None:
            raise CoordinateResolutionError(
                "registered_crs_code требует registry-aware coordinate resolution service."
            )
        if coordinate.axis_order is None:
            raise CoordinateResolutionError(
                "Для явной projected CRS необходимо указать axis_order."
            )

        source_crs = self._parse_crs(coordinate.crs)
        if not source_crs.is_projected:
            raise CoordinateResolutionError(
                "Для типа projected требуется проекционная система координат. "
                "Проверьте EPSG/CRS или используйте type=geographic."
            )

        if coordinate.axis_order == ProjectedAxisOrder.X_EASTING_Y_NORTHING:
            easting = coordinate.x
            northing = coordinate.y
        else:
            easting = coordinate.y
            northing = coordinate.x

        try:
            transformer = Transformer.from_crs(source_crs, _WGS84, always_xy=True)
            longitude, latitude = transformer.transform(easting, northing)
        except ProjError as error:
            raise CoordinateResolutionError(
                f"Не удалось преобразовать X/Y из {coordinate.crs}."
            ) from error

        self._validate_wgs84(latitude=latitude, longitude=longitude)
        return ResolvedCoordinate(
            latitude=latitude,
            longitude=longitude,
            source_crs=source_crs.to_string(),
            source_x=coordinate.x,
            source_y=coordinate.y,
            axis_order=coordinate.axis_order,
        )

    @staticmethod
    def _parse_crs(value: str) -> CRS:
        try:
            return CRS.from_user_input(value)
        except CRSError as error:
            raise CoordinateResolutionError(
                f"Неизвестная или некорректная система координат: {value}."
            ) from error

    @staticmethod
    def _validate_wgs84(*, latitude: float, longitude: float) -> None:
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise CoordinateResolutionError(
                "После преобразования получена точка вне допустимого диапазона WGS84. "
                "Проверьте CRS, зону и порядок осей X/Y."
            )
