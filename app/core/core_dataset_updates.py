from __future__ import annotations

import base64
import json
import stat
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from app.core.core_dataset_manifest import (
    CoreDatasetFileKind,
    CoreDatasetManifestError,
    validate_core_dataset_bundle,
)

CORE_DATASET_UPDATE_CHANNEL_SCHEMA_VERSION = 1


class CoreDatasetUpdateDescriptorError(ValueError):
    pass


class CoreDatasetUpdateSignatureError(CoreDatasetUpdateDescriptorError):
    pass


class CoreDatasetUpdateDescriptor(BaseModel):
    channel_schema_version: Literal[1] = 1
    dataset_code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,119}$")
    dataset_version: str = Field(min_length=1, max_length=120)
    core_dataset_schema_version: int = Field(ge=1)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bundle_url: AnyHttpUrl
    bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    published_at: datetime
    minimum_app_version: str | None = Field(default=None, max_length=120)
    required_database_revision: str | None = Field(default=None, max_length=120)
    key_id: str = Field(min_length=1, max_length=120)
    signature: str = Field(min_length=1, max_length=500)

    @field_validator("bundle_url")
    @classmethod
    def require_https_bundle_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme != "https":
            raise ValueError("Core Dataset update bundle_url must use HTTPS")
        return value


class CoreDatasetBundleIdentity(BaseModel):
    sources: frozenset[str] = frozenset()
    regions: frozenset[str] = frozenset()
    entities: frozenset[str] = frozenset()
    facts: frozenset[str] = frozenset()


def canonical_signed_payload(payload: dict[str, object]) -> bytes:
    unsigned = {key: value for key, value in payload.items() if key != "signature"}
    return json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def verify_signed_update_descriptor(
    payload: object,
    trusted_public_keys: dict[str, str],
) -> CoreDatasetUpdateDescriptor:
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise CoreDatasetUpdateDescriptorError("Core Dataset update descriptor must be a JSON object")

    raw_payload: dict[str, object] = dict(payload)
    key_id = raw_payload.get("key_id")
    signature = raw_payload.get("signature")
    if not isinstance(key_id, str) or not key_id:
        raise CoreDatasetUpdateSignatureError("Core Dataset update descriptor has no key_id")
    if not isinstance(signature, str) or not signature:
        raise CoreDatasetUpdateSignatureError("Core Dataset update descriptor has no signature")

    encoded_key = trusted_public_keys.get(key_id)
    if encoded_key is None:
        raise CoreDatasetUpdateSignatureError(f"Untrusted Core Dataset signing key: {key_id}")

    try:
        public_key_bytes = base64.b64decode(encoded_key, validate=True)
        signature_bytes = base64.b64decode(signature, validate=True)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, canonical_signed_payload(raw_payload))
    except (ValueError, InvalidSignature) as error:
        raise CoreDatasetUpdateSignatureError("Invalid Core Dataset update signature") from error

    try:
        descriptor = CoreDatasetUpdateDescriptor.model_validate(raw_payload)
    except ValueError as error:
        raise CoreDatasetUpdateDescriptorError(
            f"Invalid Core Dataset update descriptor: {error}"
        ) from error

    if descriptor.channel_schema_version != CORE_DATASET_UPDATE_CHANNEL_SCHEMA_VERSION:
        raise CoreDatasetUpdateDescriptorError(
            "Unsupported Core Dataset update channel schema version"
        )
    return descriptor


def extract_verified_update_bundle(
    bundle_bytes: bytes,
    *,
    descriptor: CoreDatasetUpdateDescriptor,
    cache_root: Path,
    max_extracted_bytes: int,
) -> Path:
    release_root = (
        cache_root
        / descriptor.dataset_code
        / f"{descriptor.dataset_version}-{descriptor.manifest_sha256[:12]}"
    )
    manifest_path = release_root / "bundle" / "manifest.json"
    if manifest_path.is_file():
        _validate_extracted_release(manifest_path, descriptor)
        return manifest_path

    cache_root.mkdir(parents=True, exist_ok=True)
    release_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="geokz-core-update-",
        dir=release_root.parent,
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        archive_path = temporary_root / "bundle.zip"
        archive_path.write_bytes(bundle_bytes)
        extraction_root = temporary_root / "bundle"
        extraction_root.mkdir(parents=True, exist_ok=True)
        _safe_extract_zip(
            archive_path,
            extraction_root,
            max_extracted_bytes=max_extracted_bytes,
        )
        temporary_manifest = extraction_root / "manifest.json"
        _validate_extracted_release(temporary_manifest, descriptor)

        if release_root.exists():
            _validate_extracted_release(manifest_path, descriptor)
            return manifest_path
        temporary_root.rename(release_root)

    _validate_extracted_release(manifest_path, descriptor)
    return manifest_path


def inspect_bundle_identity(manifest_path: Path) -> CoreDatasetBundleIdentity:
    try:
        bundle = validate_core_dataset_bundle(manifest_path)
    except CoreDatasetManifestError as error:
        raise CoreDatasetUpdateDescriptorError(str(error)) from error

    return CoreDatasetBundleIdentity(
        sources=frozenset(_jsonl_external_ids(bundle.file_paths.get(CoreDatasetFileKind.SOURCES))),
        regions=frozenset(_region_external_ids(bundle.file_paths.get(CoreDatasetFileKind.REGIONS))),
        entities=frozenset(_jsonl_external_ids(bundle.file_paths.get(CoreDatasetFileKind.ENTITIES))),
        facts=frozenset(_jsonl_external_ids(bundle.file_paths.get(CoreDatasetFileKind.FACTS))),
    )


def _safe_extract_zip(
    archive_path: Path,
    extraction_root: Path,
    *,
    max_extracted_bytes: int,
) -> None:
    total_size = 0
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                name = member.filename.replace("\\", "/")
                candidate = Path(name)
                if candidate.is_absolute() or ".." in candidate.parts:
                    raise CoreDatasetUpdateDescriptorError(
                        f"Unsafe path in Core Dataset update bundle: {member.filename}"
                    )
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise CoreDatasetUpdateDescriptorError(
                        f"Symlink is not allowed in Core Dataset update bundle: {member.filename}"
                    )
                total_size += member.file_size
                if total_size > max_extracted_bytes:
                    raise CoreDatasetUpdateDescriptorError(
                        "Core Dataset update bundle exceeds extracted-size limit"
                    )

                target = (extraction_root / candidate).resolve()
                try:
                    target.relative_to(extraction_root.resolve())
                except ValueError as error:
                    raise CoreDatasetUpdateDescriptorError(
                        f"Unsafe path in Core Dataset update bundle: {member.filename}"
                    ) from error

                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as destination:
                    while chunk := source.read(1024 * 1024):
                        destination.write(chunk)
    except zipfile.BadZipFile as error:
        raise CoreDatasetUpdateDescriptorError("Invalid Core Dataset update ZIP bundle") from error


def _validate_extracted_release(
    manifest_path: Path,
    descriptor: CoreDatasetUpdateDescriptor,
) -> None:
    if not manifest_path.is_file():
        raise CoreDatasetUpdateDescriptorError(
            "Core Dataset update bundle must contain manifest.json at archive root"
        )
    try:
        bundle = validate_core_dataset_bundle(manifest_path)
    except CoreDatasetManifestError as error:
        raise CoreDatasetUpdateDescriptorError(str(error)) from error

    if bundle.manifest_sha256 != descriptor.manifest_sha256:
        raise CoreDatasetUpdateDescriptorError(
            "Core Dataset manifest checksum does not match signed update descriptor"
        )
    if bundle.manifest.dataset_code != descriptor.dataset_code:
        raise CoreDatasetUpdateDescriptorError(
            "Core Dataset bundle dataset_code does not match signed update descriptor"
        )
    if bundle.manifest.dataset_version != descriptor.dataset_version:
        raise CoreDatasetUpdateDescriptorError(
            "Core Dataset bundle dataset_version does not match signed update descriptor"
        )
    if bundle.manifest.schema_version != descriptor.core_dataset_schema_version:
        raise CoreDatasetUpdateDescriptorError(
            "Core Dataset bundle schema_version does not match signed update descriptor"
        )


def _jsonl_external_ids(path: Path | None) -> list[str]:
    if path is None:
        return []
    result: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise CoreDatasetUpdateDescriptorError(
                f"Invalid JSONL at {path.name}:{line_number}"
            ) from error
        external_id = payload.get("external_id") if isinstance(payload, dict) else None
        if not isinstance(external_id, str) or not external_id:
            raise CoreDatasetUpdateDescriptorError(
                f"Missing external_id at {path.name}:{line_number}"
            )
        result.append(external_id)
    return result


def _region_external_ids(path: Path | None) -> list[str]:
    if path is None:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CoreDatasetUpdateDescriptorError(f"Invalid regions JSON: {path.name}") from error
    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list):
        raise CoreDatasetUpdateDescriptorError("regions FeatureCollection.features must be a list")
    result: list[str] = []
    for index, feature in enumerate(features):
        properties = feature.get("properties") if isinstance(feature, dict) else None
        external_id = properties.get("external_id") if isinstance(properties, dict) else None
        if not isinstance(external_id, str) or not external_id:
            raise CoreDatasetUpdateDescriptorError(
                f"Missing region external_id at feature #{index}"
            )
        result.append(external_id)
    return result
