import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from app.application.core_dataset import CoreDatasetImportError, validate_core_dataset
from app.application.core_dataset_management import CoreDatasetManagementService
from app.core.core_dataset_manifest import DEFAULT_CORE_DATASET_MANIFEST
from app.core.database import AsyncSessionFactory


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))


def _manifest_path(value: str | None) -> Path:
    return Path(value).resolve() if value else DEFAULT_CORE_DATASET_MANIFEST


def validate_command(manifest: Path) -> int:
    result = validate_core_dataset(manifest)
    _print_json(asdict(result))
    return 0


async def install_command(manifest: Path, *, dry_run: bool) -> int:
    async with AsyncSessionFactory() as session:
        result = await CoreDatasetManagementService(session, manifest).install(dry_run=dry_run)
        _print_json(asdict(result))
    return 0


async def status_command(manifest: Path) -> int:
    async with AsyncSessionFactory() as session:
        result = await CoreDatasetManagementService(session, manifest).status()
        installed = None
        if result.installed is not None:
            installed = {
                "dataset_code": result.installed.dataset_code,
                "dataset_version": result.installed.dataset_version,
                "schema_version": result.installed.schema_version,
                "manifest_sha256": result.installed.manifest_sha256,
                "installed_at": result.installed.installed_at,
                "file_checksums": dict(result.installed.file_checksums),
                "item_counts": dict(result.installed.item_counts),
            }
        _print_json(
            {
                "dataset_code": result.dataset_code,
                "bundled_version": result.bundled_version,
                "schema_version": result.schema_version,
                "manifest_sha256": result.manifest_sha256,
                "minimum_app_version": result.minimum_app_version,
                "dependencies": result.dependencies,
                "installed": installed,
                "update_available": result.update_available,
            }
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, install, or inspect the versioned GeoKZ Core Dataset."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate manifest and payloads")
    validate_parser.add_argument("manifest", nargs="?", help="Path to manifest.json")

    install_parser = subparsers.add_parser("install", help="Install the Core Dataset")
    install_parser.add_argument("manifest", nargs="?", help="Path to manifest.json")
    install_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and parse without writing database changes",
    )

    status_parser = subparsers.add_parser("status", help="Show bundled and installed versions")
    status_parser.add_argument("manifest", nargs="?", help="Path to manifest.json")
    return parser


async def _run(args: argparse.Namespace) -> int:
    manifest = _manifest_path(args.manifest)
    if args.command == "validate":
        return validate_command(manifest)
    if args.command == "install":
        return await install_command(manifest, dry_run=args.dry_run)
    if args.command == "status":
        return await status_command(manifest)
    raise RuntimeError(f"Unsupported command: {args.command}")


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(_run(args))
    except CoreDatasetImportError as error:
        print(f"Core Dataset error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
