import hashlib
import json
from pathlib import Path

import pytest

from app.application.core_dataset import CoreDatasetImportError, validate_core_dataset
from app.core.core_dataset_manifest import (
    DEFAULT_CORE_DATASET_MANIFEST,
    CoreDatasetManifestError,
    validate_core_dataset_bundle,
)


def _write_manifest(
    root: Path,
    *,
    files: list[dict[str, object]],
    schema_version: int = 1,
) -> Path:
    manifest = {
        "dataset_code": "geokz-core-test",
        "dataset_version": "test-1",
        "schema_version": schema_version,
        "created_at": "2026-09-05T00:00:00Z",
        "external_id_prefix": "geokz-core-test:",
        "dependencies": {},
        "files": files,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _file_entry(path: Path, kind: str) -> dict[str, object]:
    return {
        "path": path.name,
        "kind": kind,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "required": True,
    }


def test_bundled_core_dataset_validates() -> None:
    result = validate_core_dataset(DEFAULT_CORE_DATASET_MANIFEST)

    assert result.dataset_code == "geokz-core"
    assert result.dataset_version == "2026.09.0-bootstrap"
    assert result.schema_version == 1
    assert result.item_counts == {
        "sources": 1,
        "regions": 1,
        "entities": 0,
        "facts": 0,
    }
    assert result.dry_run is True


def test_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    data_path = tmp_path / "sources.jsonl"
    data_path.write_text("{}\n", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        files=[
            {
                "path": data_path.name,
                "kind": "sources",
                "sha256": "0" * 64,
                "required": True,
            }
        ],
    )

    with pytest.raises(CoreDatasetManifestError, match="Checksum mismatch"):
        validate_core_dataset_bundle(manifest_path)


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        files=[
            {
                "path": "../outside.jsonl",
                "kind": "sources",
                "sha256": "0" * 64,
                "required": True,
            }
        ],
    )

    with pytest.raises(CoreDatasetManifestError, match="inside the bundle"):
        validate_core_dataset_bundle(manifest_path)


def test_unsupported_schema_version_is_rejected(tmp_path: Path) -> None:
    data_path = tmp_path / "sources.jsonl"
    data_path.write_text("", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        schema_version=999,
        files=[_file_entry(data_path, "sources")],
    )

    with pytest.raises(CoreDatasetManifestError, match="Unsupported Core Dataset schema_version"):
        validate_core_dataset_bundle(manifest_path)


def test_duplicate_external_ids_are_rejected(tmp_path: Path) -> None:
    source = {
        "external_id": "geokz-core-test:source:duplicate",
        "title": "Duplicate test source",
        "document_type": "dataset",
        "access_level": "LOCAL",
        "reliability_level": "A",
    }
    data_path = tmp_path / "sources.jsonl"
    data_path.write_text(
        json.dumps(source) + "\n" + json.dumps(source) + "\n",
        encoding="utf-8",
    )
    manifest_path = _write_manifest(
        tmp_path,
        files=[_file_entry(data_path, "sources")],
    )

    with pytest.raises(CoreDatasetImportError, match="Duplicate source external_id"):
        validate_core_dataset(manifest_path)


def test_unknown_fact_source_reference_is_rejected(tmp_path: Path) -> None:
    fact = {
        "external_id": "geokz-core-test:fact:orphan",
        "primary_source_external_id": "geokz-core-test:source:missing",
        "entity_type": "field",
        "category": "geography",
        "original_text": "Test fact",
        "normalized_statement": "Test fact",
        "fact_kind": "OBSERVATION",
    }
    data_path = tmp_path / "facts.jsonl"
    data_path.write_text(json.dumps(fact) + "\n", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        files=[_file_entry(data_path, "facts")],
    )

    with pytest.raises(CoreDatasetImportError, match="Unknown fact primary_source_external_id"):
        validate_core_dataset(manifest_path)
