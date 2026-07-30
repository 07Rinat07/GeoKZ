from enum import StrEnum

from sqlalchemy import Enum


def enum_type[EnumT: StrEnum](enum_class: type[EnumT], name: str) -> Enum:
    """Хранит строковые значения Enum, а не имена Python-констант."""

    return Enum(
        enum_class,
        values_callable=lambda values: [item.value for item in values],
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        name=name,
    )


class SourceDocumentType(StrEnum):
    REPORT = "report"
    BOOK = "book"
    ARTICLE = "article"
    MAP = "map"
    REGISTRY = "registry"
    THESIS = "thesis"
    PROJECT = "project"
    DATASET = "dataset"
    WEB_PAGE = "web_page"


class AccessLevel(StrEnum):
    FULL = "FULL"
    ABSTRACT_ONLY = "ABSTRACT_ONLY"
    METADATA_ONLY = "METADATA_ONLY"
    PAID = "PAID"
    RESTRICTED = "RESTRICTED"
    LOCAL = "LOCAL"


class ReliabilityLevel(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class VerificationStatus(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    VERIFIED = "VERIFIED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    OBSOLETE = "OBSOLETE"


class GeometryStatus(StrEnum):
    EXACT = "EXACT"
    APPROXIMATE = "APPROXIMATE"
    DIGITIZED = "DIGITIZED"
    UNKNOWN = "UNKNOWN"


class EntityNameType(StrEnum):
    CANONICAL = "canonical"
    HISTORICAL = "historical"
    TRANSLITERATION = "transliteration"
    ABBREVIATION = "abbreviation"
    OCR_VARIANT = "ocr_variant"
    SYNONYM = "synonym"


class ExtractionStatus(StrEnum):
    PENDING = "PENDING"
    EXTRACTED = "EXTRACTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class ExtractionMethod(StrEnum):
    PDF_TEXT = "pdf_text"
    OCR = "ocr"
    DOCX = "docx"
    CSV = "csv"
    MANUAL = "manual"
    IMPORT = "import"


class FactCategory(StrEnum):
    TECTONICS = "tectonics"
    STRATIGRAPHY = "stratigraphy"
    LITHOLOGY = "lithology"
    HYDROCARBON = "hydrocarbon"
    WATER = "water"
    WELL = "well"
    MAP = "map"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ENVIRONMENT = "environment"


class FactKind(StrEnum):
    OBSERVATION = "OBSERVATION"
    MEASUREMENT = "MEASUREMENT"
    INTERPRETATION = "INTERPRETATION"
    FORECAST = "FORECAST"
    HISTORICAL = "HISTORICAL"


class ConfidenceLevel(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


class EvidenceRole(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    MENTIONS = "mentions"
    CONTEXTUALIZES = "contextualizes"


class WellType(StrEnum):
    STRUCTURAL = "structural"
    EXPLORATION = "exploration"
    APPRAISAL = "appraisal"
    PRODUCTION = "production"
    HYDROGEOLOGICAL = "hydrogeological"
    OTHER = "other"


class CoordinateAccuracy(StrEnum):
    EXACT = "EXACT"
    APPROXIMATE = "APPROXIMATE"
    DIGITIZED = "DIGITIZED"
    UNKNOWN = "UNKNOWN"


class DepthReference(StrEnum):
    MD = "MD"
    TVD = "TVD"
    TVDSS = "TVDSS"
    UNKNOWN = "UNKNOWN"


class FluidType(StrEnum):
    OIL = "OIL"
    GAS = "GAS"
    CONDENSATE = "CONDENSATE"
    WATER = "WATER"
    BRINE = "BRINE"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class HydrocarbonStatus(StrEnum):
    COMMERCIAL_FIELD = "COMMERCIAL_FIELD"
    DISCOVERED_ACCUMULATION = "DISCOVERED_ACCUMULATION"
    TESTED_FLOW = "TESTED_FLOW"
    LOG_INTERPRETATION = "LOG_INTERPRETATION"
    OIL_SHOW = "OIL_SHOW"
    GAS_SHOW = "GAS_SHOW"
    BITUMEN_SHOW = "BITUMEN_SHOW"
    PROSPECTIVE = "PROSPECTIVE"
    PREDICTED = "PREDICTED"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"


class ConflictType(StrEnum):
    VALUE = "VALUE"
    GEOMETRY = "GEOMETRY"
    AGE = "AGE"
    STATUS = "STATUS"
    TERMINOLOGY = "TERMINOLOGY"
    OTHER = "OTHER"


class ConflictStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
