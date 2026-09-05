import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

CORE_DATASET_SCHEMA_VERSION = 1
DEFAULT_CORE_DATASET_MANIFEST = (
    Path(__file__).resolve().parents[2] / "data" / "bootstrap" / "core_dataset" / "manifest.json"
)


class CoreDatasetManifestError(ValueError):
    pass


class CoreDatasetFileKind(StrEnum):
    SOURCES = "sources"
    ENTITIES = "entities"
    FACTS = "facts"
    REGIONS = "regions"


class CoreDatasetManifestFile(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    kind: CoreDatasetFileKind
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    required: bool = True

    @field_validator("path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        candidate = Path(value)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("Core Dataset file path must stay inside the bundle")
        return candidate.as_posix()


class CoreDatasetManifest(BaseModel):
    dataset_code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,119}$")
    dataset_version: str = Field(min_length=1, max_length=120)
    schema_version: int = Field(ge=1)
    created_at: datetime
    minimum_app_version: str | None = Field(default=None, max_length=120)
    external_id_prefix: str = Field(default="geokz-core:", min_length=1, max_length=100)
    dependencies: dict[str, str] = Field(default_factory=dict)
    files: list[CoreDatasetManifestFile]

    @model_validator(mode="after")
    def validate_unique_files_and_kinds(self) -> "CoreDatasetManifest":
        if not self.files:
            raise ValueError("Core Dataset manifest must contain at least one file")
        paths = [item.path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("Core Dataset manifest contains duplicate file paths")
        kinds = [item.kind for item in self.files]
        if len(kinds) != len(set(kinds)):
            raise ValueError("Core Dataset manifest supports one file per kind")
        return self


@dataclass(frozen=True, slots=True)
class ValidatedCoreDatasetBundle:
    root: Path
    manifest_path: Path
    manifest: CoreDatasetManifest
    manifest_sha256: str
    file_paths: dict[CoreDatasetFileKind, Path]
    file_checksums: dict[str, str]


def load_core_dataset_manifest(path: Path = DEFAULT_CORE_DATASET_MANIFEST) -> CoreDatasetManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return CoreDatasetManifest.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise CoreDatasetManifestError(f"Invalid Core Dataset manifest {path}: {error}") from error


def validate_core_dataset_bundle(
    manifest_path: Path = DEFAULT_CORE_DATASET_MANIFEST,
) -> ValidatedCoreDatasetBundle:
    manifest_path = manifest_path.resolve()
    root = manifest_path.parent.resolve()
    manifest_bytes = _read_bytes(manifest_path, "manifest")
    try:
        manifest_payload = json.loads(manifest_bytes.decode("utf-8"))
        manifest = CoreDatasetManifest.model_validate(manifest_payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise CoreDatasetManifestError(f"Invalid Core Dataset manifest: {error}") from error

    if manifest.schema_version != CORE_DATASET_SCHEMA_VERSION:
        raise CoreDatasetManifestError(
            "Unsupported Core Dataset schema_version "
            f"{manifest.schema_version}; supported={CORE_DATASET_SCHEMA_VERSION}"
        )

    file_paths: dict[CoreDatasetFileKind, Path] = {}
    file_checksums: dict[str, str] = {}
    for item in manifest.files:
        candidate = (root / item.path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise CoreDatasetManifestError(
                f"Core Dataset file escapes bundle root: {item.path}"
            ) from error

        if not candidate.is_file():
            if item.required:
                raise CoreDatasetManifestError(f"Required Core Dataset file is missing: {item.path}")
            continue

        content = _read_bytes(candidate, item.path)
        digest = hashlib.sha256(content).hexdigest()
        if digest != item.sha256:
            raise CoreDatasetManifestError(
                f"Checksum mismatch for {item.path}: expected={item.sha256}, actual={digest}"
            )
        file_paths[item.kind] = candidate
        file_checksums[item.path] = digest

    return ValidatedCoreDatasetBundle(
        root=root,
        manifest_path=manifest_path,
        manifest=manifest,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        file_paths=file_paths,
        file_checksums=file_checksums,
    )


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise CoreDatasetManifestError(f"Cannot read Core Dataset {label}: {error}") from error
