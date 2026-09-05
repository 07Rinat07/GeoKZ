import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.core_dataset_updates import (
    CoreDatasetUpdateDescriptorError,
    CoreDatasetUpdateSignatureError,
    canonical_signed_payload,
    extract_verified_update_bundle,
    inspect_bundle_identity,
    verify_signed_update_descriptor,
)


def _release_fixture() -> tuple[dict[str, object], dict[str, str], bytes]:
    sources = b""
    manifest_bytes = json.dumps(
        {
            "dataset_code": "geokz-core",
            "dataset_version": "2026.09.1-test",
            "schema_version": 1,
            "created_at": "2026-09-05T00:00:00Z",
            "minimum_app_version": "0.2.0-dev",
            "external_id_prefix": "geokz-core:",
            "dependencies": {},
            "files": [
                {
                    "path": "sources.jsonl",
                    "kind": "sources",
                    "sha256": hashlib.sha256(sources).hexdigest(),
                }
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        archive.writestr("sources.jsonl", sources)
    bundle_bytes = archive_buffer.getvalue()

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    payload: dict[str, object] = {
        "channel_schema_version": 1,
        "dataset_code": "geokz-core",
        "dataset_version": "2026.09.1-test",
        "core_dataset_schema_version": 1,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "bundle_url": "https://updates.example/geokz/core/2026.09.1-test.zip",
        "bundle_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "published_at": "2026-09-05T00:00:00Z",
        "minimum_app_version": "0.2.0-dev",
        "required_database_revision": "20260905_0011",
        "key_id": "test-key-1",
    }
    payload["signature"] = base64.b64encode(
        private_key.sign(canonical_signed_payload(payload))
    ).decode("ascii")
    trusted = {"test-key-1": base64.b64encode(public_key).decode("ascii")}
    return payload, trusted, bundle_bytes


def test_signed_descriptor_verifies_and_tampering_is_rejected() -> None:
    payload, trusted, _bundle_bytes = _release_fixture()

    descriptor = verify_signed_update_descriptor(payload, trusted)
    assert descriptor.dataset_version == "2026.09.1-test"
    assert descriptor.key_id == "test-key-1"

    tampered = dict(payload)
    tampered["dataset_version"] = "2026.09.9-tampered"
    with pytest.raises(CoreDatasetUpdateSignatureError):
        verify_signed_update_descriptor(tampered, trusted)


def test_descriptor_rejects_untrusted_key_and_non_https_bundle() -> None:
    payload, _trusted, _bundle_bytes = _release_fixture()
    with pytest.raises(CoreDatasetUpdateSignatureError):
        verify_signed_update_descriptor(payload, {})

    payload, trusted, _bundle_bytes = _release_fixture()
    payload["bundle_url"] = "http://updates.example/geokz/core.zip"
    # Re-sign so the URL validation, rather than signature tampering, is what rejects it.
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    payload["key_id"] = "http-test"
    payload["signature"] = base64.b64encode(
        private_key.sign(canonical_signed_payload(payload))
    ).decode("ascii")
    trusted = {"http-test": base64.b64encode(public_key).decode("ascii")}
    with pytest.raises(CoreDatasetUpdateDescriptorError):
        verify_signed_update_descriptor(payload, trusted)


def test_verified_bundle_is_extracted_and_identity_can_be_inspected(tmp_path: Path) -> None:
    payload, trusted, bundle_bytes = _release_fixture()
    descriptor = verify_signed_update_descriptor(payload, trusted)

    manifest_path = extract_verified_update_bundle(
        bundle_bytes,
        descriptor=descriptor,
        cache_root=tmp_path / "cache",
        max_extracted_bytes=1024 * 1024,
    )

    assert manifest_path.is_file()
    identity = inspect_bundle_identity(manifest_path)
    assert identity.sources == frozenset()
    assert identity.regions == frozenset()
    assert identity.entities == frozenset()
    assert identity.facts == frozenset()


def test_bundle_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    payload, trusted, _bundle_bytes = _release_fixture()
    descriptor = verify_signed_update_descriptor(payload, trusted)

    malicious = io.BytesIO()
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../escape.txt", "no")

    with pytest.raises(CoreDatasetUpdateDescriptorError, match="Unsafe path"):
        extract_verified_update_bundle(
            malicious.getvalue(),
            descriptor=descriptor,
            cache_root=tmp_path / "cache",
            max_extracted_bytes=1024 * 1024,
        )
