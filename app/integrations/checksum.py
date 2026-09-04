import hashlib
import json
from collections.abc import Mapping
from typing import Any


def calculate_payload_checksum(payload: Mapping[str, Any]) -> str:
    """Возвращает стабильный SHA-256 для JSON-совместимой записи внешнего источника."""

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
