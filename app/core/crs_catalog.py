from dataclasses import dataclass

from app.core.project_info import SupportedLanguage
from app.schemas.coordinates import ProjectedAxisOrder
from app.schemas.crs import CrsPreset, CrsPresetListResponse


@dataclass(frozen=True, slots=True)
class _PresetDefinition:
    code: str
    epsg: int
    coordinate_type: str
    longitude_range: str | None = None
    default_axis_order: ProjectedAxisOrder | None = None


_PRESETS: tuple[_PresetDefinition, ...] = (
    _PresetDefinition(
        code="wgs84-geographic",
        epsg=4326,
        coordinate_type="geographic",
    ),
    *(
        _PresetDefinition(
            code=f"wgs84-utm-{zone}n",
            epsg=32600 + zone,
            coordinate_type="projected",
            longitude_range=f"{zone * 6 - 186}°E–{zone * 6 - 180}°E",
            default_axis_order=ProjectedAxisOrder.X_EASTING_Y_NORTHING,
        )
        for zone in range(38, 46)
    ),
)


def _display_name(preset: _PresetDefinition, language: SupportedLanguage) -> str:
    if preset.epsg == 4326:
        return {
            "ru": "WGS 84 — широта/долгота",
            "kk": "WGS 84 — ендік/бойлық",
            "en": "WGS 84 — latitude/longitude",
        }[language]

    zone = preset.epsg - 32600
    return {
        "ru": f"WGS 84 / UTM зона {zone}N",
        "kk": f"WGS 84 / UTM {zone}N аймағы",
        "en": f"WGS 84 / UTM zone {zone}N",
    }[language]


def get_crs_presets(language: SupportedLanguage) -> CrsPresetListResponse:
    warning = {
        "ru": (
            "Диапазон долготы помогает сузить выбор UTM-зоны, но не доказывает, что исходный "
            "документ использует WGS84/UTM. CRS необходимо подтверждать по паспорту координат, "
            "карте, проекту или данным предприятия. СК-42/Гаусса–Крюгера и локальные системы "
            "вводятся по точному EPSG/WKT/PROJ-описанию."
        ),
        "kk": (
            "Бойлық диапазоны UTM аймағын таңдауға көмектеседі, бірақ бастапқы құжаттың WGS84/UTM "
            "қолданғанын дәлелдемейді. CRS координат паспорты, карта, жоба немесе кәсіпорын деректері "
            "бойынша расталуы тиіс. СК-42/Гаусс–Крюгер және жергілікті жүйелер нақты EPSG/WKT/PROJ "
            "сипаттамасымен енгізіледі."
        ),
        "en": (
            "Longitude coverage helps narrow the UTM zone but does not prove that the source document "
            "uses WGS84/UTM. Confirm the CRS from coordinate metadata, maps, project documentation or "
            "company data. SK-42/Gauss-Kruger and local systems require an exact EPSG/WKT/PROJ definition."
        ),
    }[language]

    return CrsPresetListResponse(
        language=language,
        presets=[
            CrsPreset(
                code=preset.code,
                epsg=preset.epsg,
                coordinate_type=preset.coordinate_type,
                display_name=_display_name(preset, language),
                longitude_range=preset.longitude_range,
                default_axis_order=preset.default_axis_order,
                requires_source_confirmation=True,
            )
            for preset in _PRESETS
        ],
        warning=warning,
    )
