import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.core_dataset_manifest import (
    CoreDatasetFileKind,
    CoreDatasetManifestError,
    ValidatedCoreDatasetBundle,
    validate_core_dataset_bundle,
)
from app.models.administrative_region import AdministrativeRegion
from app.models.core_dataset import CoreDatasetState
from app.models.entity import GeologicalEntity
from app.models.enums import (
    AccessLevel,
    ConfidenceLevel,
    FactCategory,
    FactKind,
    GeometryStatus,
    ReliabilityLevel,
    SourceDocumentType,
    VerificationStatus,
)
from app.models.fact import Fact
from app.models.source import Source


class CoreDatasetImportError(ValueError):
    pass


class CoreSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str
    title: str = Field(min_length=1)
    authors: list[str] = Field(default_factory=list)
    organization: str | None = None
    publication_year: int | None = Field(default=None, ge=1500, le=2100)
    survey_year_start: int | None = Field(default=None, ge=1500, le=2100)
    survey_year_end: int | None = Field(default=None, ge=1500, le=2100)
    document_type: SourceDocumentType
    language: str = "ru"
    territories: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    inventory_number: str | None = None
    doi: str | None = None
    url: str | None = None
    access_date: date | None = None
    access_level: AccessLevel = AccessLevel.LOCAL
    page_count: int | None = Field(default=None, ge=1)
    map_scale: str | None = None
    coordinate_system: str | None = None
    license: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    reliability_level: ReliabilityLevel
    notes: str | None = None


class CoreRegionProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str
    level: str = Field(min_length=1, max_length=64)
    name_ru: str = Field(min_length=1)
    name_kk: str | None = None
    name_en: str | None = None
    notes: str | None = None
    parent_external_id: str | None = None


class CoreEntityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str
    object_type: str = Field(min_length=1, max_length=80)
    parent_external_id: str | None = None
    name_ru: str = Field(min_length=1)
    name_kk: str | None = None
    name_en: str | None = None
    description: str | None = None
    geological_context: dict[str, Any] = Field(default_factory=dict)
    geometry: dict[str, Any] | None = None
    geometry_status: GeometryStatus = GeometryStatus.UNKNOWN
    geometry_source_external_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.DRAFT


class CoreFactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str
    primary_source_external_id: str
    entity_external_id: str | None = None
    entity_type: str = Field(min_length=1, max_length=80)
    category: FactCategory
    original_text: str = Field(min_length=1)
    normalized_statement: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    figure_number: str | None = None
    table_number: str | None = None
    section_title: str | None = None
    methods: list[str] = Field(default_factory=list)
    fact_kind: FactKind
    valid_time_start: int | None = None
    valid_time_end: int | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    needs_human_review: bool = True
    review_reason: str | None = None
    verification_status: VerificationStatus = VerificationStatus.DRAFT
    related_fact_ids: list[str] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ParsedCoreDataset:
    sources: list[CoreSourceRecord]
    regions: list[tuple[CoreRegionProperties, dict[str, Any] | None]]
    entities: list[CoreEntityRecord]
    facts: list[CoreFactRecord]

    @property
    def counts(self) -> dict[str, int]:
        return {
            "sources": len(self.sources),
            "regions": len(self.regions),
            "entities": len(self.entities),
            "facts": len(self.facts),
        }


@dataclass(frozen=True, slots=True)
class CoreDatasetImportResult:
    dataset_code: str
    dataset_version: str
    schema_version: int
    manifest_sha256: str
    installed_at: datetime | None
    item_counts: dict[str, int]
    changed: bool
    dry_run: bool


@dataclass(slots=True)
class CoreDatasetImporter:
    session: AsyncSession

    async def import_bundle(
        self,
        manifest_path: Path,
        *,
        dry_run: bool = False,
    ) -> CoreDatasetImportResult:
        bundle = validate_core_dataset_bundle(manifest_path)
        parsed = self._parse_bundle(bundle)
        self._validate_namespace_and_references(bundle, parsed)

        existing_state = await self.session.scalar(
            select(CoreDatasetState).where(
                CoreDatasetState.dataset_code == bundle.manifest.dataset_code
            )
        )
        if (
            existing_state is not None
            and existing_state.manifest_sha256 == bundle.manifest_sha256
        ):
            return CoreDatasetImportResult(
                dataset_code=existing_state.dataset_code,
                dataset_version=existing_state.dataset_version,
                schema_version=existing_state.schema_version,
                manifest_sha256=existing_state.manifest_sha256,
                installed_at=existing_state.installed_at,
                item_counts=dict(existing_state.item_counts),
                changed=False,
                dry_run=dry_run,
            )

        if dry_run:
            return CoreDatasetImportResult(
                dataset_code=bundle.manifest.dataset_code,
                dataset_version=bundle.manifest.dataset_version,
                schema_version=bundle.manifest.schema_version,
                manifest_sha256=bundle.manifest_sha256,
                installed_at=None,
                item_counts=parsed.counts,
                changed=True,
                dry_run=True,
            )

        try:
            source_ids = await self._upsert_sources(parsed.sources)
            region_ids = await self._upsert_regions(parsed.regions)
            entity_ids = await self._upsert_entities(parsed.entities, source_ids)
            await self._upsert_facts(parsed.facts, source_ids, entity_ids)

            # Keep the local variables referenced: their construction is part of the
            # referential-integrity validation performed by the importer.
            _ = region_ids

            installed_at = datetime.now(UTC)
            if existing_state is None:
                existing_state = CoreDatasetState(dataset_code=bundle.manifest.dataset_code)
                self.session.add(existing_state)

            existing_state.dataset_version = bundle.manifest.dataset_version
            existing_state.schema_version = bundle.manifest.schema_version
            existing_state.manifest_sha256 = bundle.manifest_sha256
            existing_state.installed_at = installed_at
            existing_state.source_path = str(bundle.manifest_path)
            existing_state.file_checksums = dict(bundle.file_checksums)
            existing_state.item_counts = parsed.counts
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return CoreDatasetImportResult(
            dataset_code=bundle.manifest.dataset_code,
            dataset_version=bundle.manifest.dataset_version,
            schema_version=bundle.manifest.schema_version,
            manifest_sha256=bundle.manifest_sha256,
            installed_at=installed_at,
            item_counts=parsed.counts,
            changed=True,
            dry_run=False,
        )

    async def get_state(self, dataset_code: str = "geokz-core") -> CoreDatasetState | None:
        return await self.session.scalar(
            select(CoreDatasetState).where(CoreDatasetState.dataset_code == dataset_code)
        )

    def _parse_bundle(self, bundle: ValidatedCoreDatasetBundle) -> ParsedCoreDataset:
        try:
            sources = [
                CoreSourceRecord.model_validate(item)
                for item in self._read_jsonl(bundle, CoreDatasetFileKind.SOURCES)
            ]
            entities = [
                CoreEntityRecord.model_validate(item)
                for item in self._read_jsonl(bundle, CoreDatasetFileKind.ENTITIES)
            ]
            facts = [
                CoreFactRecord.model_validate(item)
                for item in self._read_jsonl(bundle, CoreDatasetFileKind.FACTS)
            ]
            regions = self._read_regions(bundle)
        except (ValueError, json.JSONDecodeError) as error:
            raise CoreDatasetImportError(f"Invalid Core Dataset payload: {error}") from error
        return ParsedCoreDataset(
            sources=sources,
            regions=regions,
            entities=entities,
            facts=facts,
        )

    @staticmethod
    def _read_jsonl(
        bundle: ValidatedCoreDatasetBundle,
        kind: CoreDatasetFileKind,
    ) -> list[dict[str, Any]]:
        path = bundle.file_paths.get(kind)
        if path is None:
            return []
        rows: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise CoreDatasetImportError(
                    f"{path.name}:{line_number} must contain a JSON object"
                )
            rows.append(payload)
        return rows

    @staticmethod
    def _read_regions(
        bundle: ValidatedCoreDatasetBundle,
    ) -> list[tuple[CoreRegionProperties, dict[str, Any] | None]]:
        path = bundle.file_paths.get(CoreDatasetFileKind.REGIONS)
        if path is None:
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
            raise CoreDatasetImportError("regions file must be a GeoJSON FeatureCollection")
        features = payload.get("features")
        if not isinstance(features, list):
            raise CoreDatasetImportError("regions FeatureCollection.features must be a list")

        result: list[tuple[CoreRegionProperties, dict[str, Any] | None]] = []
        for index, feature in enumerate(features):
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise CoreDatasetImportError(f"regions feature #{index} is invalid")
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                raise CoreDatasetImportError(f"regions feature #{index} has no properties")
            geometry = feature.get("geometry")
            if geometry is not None and not isinstance(geometry, dict):
                raise CoreDatasetImportError(f"regions feature #{index} has invalid geometry")
            result.append((CoreRegionProperties.model_validate(properties), geometry))
        return result

    @staticmethod
    def _validate_namespace_and_references(
        bundle: ValidatedCoreDatasetBundle,
        parsed: ParsedCoreDataset,
    ) -> None:
        prefix = bundle.manifest.external_id_prefix
        source_ids = {row.external_id for row in parsed.sources}
        region_ids = {row.external_id for row, _ in parsed.regions}
        entity_ids = {row.external_id for row in parsed.entities}
        fact_ids = {row.external_id for row in parsed.facts}

        for kind, values in {
            "source": source_ids,
            "region": region_ids,
            "entity": entity_ids,
            "fact": fact_ids,
        }.items():
            for external_id in values:
                if not external_id.startswith(prefix):
                    raise CoreDatasetImportError(
                        f"{kind} external_id must use Core Dataset namespace {prefix!r}: {external_id}"
                    )

        for row, _ in parsed.regions:
            if row.parent_external_id and row.parent_external_id not in region_ids:
                raise CoreDatasetImportError(
                    f"Unknown region parent_external_id: {row.parent_external_id}"
                )

        for row in parsed.entities:
            if row.parent_external_id and row.parent_external_id not in entity_ids:
                raise CoreDatasetImportError(
                    f"Unknown entity parent_external_id: {row.parent_external_id}"
                )
            if (
                row.geometry_source_external_id
                and row.geometry_source_external_id not in source_ids
            ):
                raise CoreDatasetImportError(
                    "Unknown entity geometry_source_external_id: "
                    f"{row.geometry_source_external_id}"
                )

        for row in parsed.facts:
            if row.primary_source_external_id not in source_ids:
                raise CoreDatasetImportError(
                    f"Unknown fact primary_source_external_id: {row.primary_source_external_id}"
                )
            if row.entity_external_id and row.entity_external_id not in entity_ids:
                raise CoreDatasetImportError(
                    f"Unknown fact entity_external_id: {row.entity_external_id}"
                )
            for related_id in row.related_fact_ids:
                if related_id not in fact_ids:
                    raise CoreDatasetImportError(f"Unknown related fact external_id: {related_id}")

    async def _upsert_sources(self, rows: list[CoreSourceRecord]) -> dict[str, Any]:
        ids: dict[str, Any] = {}
        for row in rows:
            source = await self.session.scalar(
                select(Source).where(Source.external_id == row.external_id)
            )
            values = row.model_dump()
            if source is None:
                source = Source(**values)
                self.session.add(source)
                await self.session.flush()
            else:
                for field, value in values.items():
                    setattr(source, field, value)
            ids[row.external_id] = source.id
        return ids

    async def _upsert_regions(
        self,
        rows: list[tuple[CoreRegionProperties, dict[str, Any] | None]],
    ) -> dict[str, Any]:
        ids: dict[str, Any] = {}
        objects: dict[str, AdministrativeRegion] = {}
        for row, geometry in rows:
            region = await self.session.scalar(
                select(AdministrativeRegion).where(
                    AdministrativeRegion.external_id == row.external_id
                )
            )
            if region is None:
                region = AdministrativeRegion(
                    external_id=row.external_id,
                    level=row.level,
                    name_ru=row.name_ru,
                )
                self.session.add(region)
                await self.session.flush()
            region.level = row.level
            region.name_ru = row.name_ru
            region.name_kk = row.name_kk
            region.name_en = row.name_en
            region.notes = row.notes
            region.geometry = self._geojson_expression(geometry, multipolygon=True)
            ids[row.external_id] = region.id
            objects[row.external_id] = region

        for row, _ in rows:
            objects[row.external_id].parent_id = (
                ids[row.parent_external_id] if row.parent_external_id else None
            )
        return ids

    async def _upsert_entities(
        self,
        rows: list[CoreEntityRecord],
        source_ids: dict[str, Any],
    ) -> dict[str, Any]:
        ids: dict[str, Any] = {}
        objects: dict[str, GeologicalEntity] = {}
        for row in rows:
            entity = await self.session.scalar(
                select(GeologicalEntity).where(GeologicalEntity.external_id == row.external_id)
            )
            if entity is None:
                entity = GeologicalEntity(
                    external_id=row.external_id,
                    object_type=row.object_type,
                    name_ru=row.name_ru,
                )
                self.session.add(entity)
                await self.session.flush()
            entity.object_type = row.object_type
            entity.name_ru = row.name_ru
            entity.name_kk = row.name_kk
            entity.name_en = row.name_en
            entity.description = row.description
            entity.geological_context = row.geological_context
            entity.geometry = self._geojson_expression(row.geometry)
            entity.geometry_status = row.geometry_status
            entity.geometry_source_id = (
                source_ids[row.geometry_source_external_id]
                if row.geometry_source_external_id
                else None
            )
            entity.verification_status = row.verification_status
            ids[row.external_id] = entity.id
            objects[row.external_id] = entity

        for row in rows:
            objects[row.external_id].parent_id = (
                ids[row.parent_external_id] if row.parent_external_id else None
            )
        return ids

    async def _upsert_facts(
        self,
        rows: list[CoreFactRecord],
        source_ids: dict[str, Any],
        entity_ids: dict[str, Any],
    ) -> None:
        for row in rows:
            fact = await self.session.scalar(select(Fact).where(Fact.external_id == row.external_id))
            values = row.model_dump(
                exclude={"primary_source_external_id", "entity_external_id"}
            )
            values["primary_source_id"] = source_ids[row.primary_source_external_id]
            values["entity_id"] = (
                entity_ids[row.entity_external_id] if row.entity_external_id else None
            )
            if fact is None:
                self.session.add(Fact(**values))
            else:
                for field, value in values.items():
                    setattr(fact, field, value)

    @staticmethod
    def _geojson_expression(
        geometry: dict[str, Any] | None,
        *,
        multipolygon: bool = False,
    ) -> Any:
        if geometry is None:
            return None
        serialized = json.dumps(geometry, ensure_ascii=False, separators=(",", ":"))
        expression = func.ST_SetSRID(func.ST_GeomFromGeoJSON(serialized), 4326)
        return func.ST_Multi(expression) if multipolygon else expression


def validate_core_dataset(manifest_path: Path) -> CoreDatasetImportResult:
    """Synchronous manifest/checksum/payload validation without database access."""

    bundle = validate_core_dataset_bundle(manifest_path)
    # Use a lightweight parser instance without touching its session; only parsing and
    # namespace/reference validation are exercised here.
    importer = object.__new__(CoreDatasetImporter)
    parsed = importer._parse_bundle(bundle)
    importer._validate_namespace_and_references(bundle, parsed)
    return CoreDatasetImportResult(
        dataset_code=bundle.manifest.dataset_code,
        dataset_version=bundle.manifest.dataset_version,
        schema_version=bundle.manifest.schema_version,
        manifest_sha256=bundle.manifest_sha256,
        installed_at=None,
        item_counts=parsed.counts,
        changed=True,
        dry_run=True,
    )
