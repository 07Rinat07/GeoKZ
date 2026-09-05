import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.enums import VocabularyCode
from app.models.vocabulary import ControlledVocabularyTerm

BOOTSTRAP_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "bootstrap"
    / "controlled_vocabularies.json"
)

_REQUIRED_FIELDS = {
    "vocabulary",
    "code",
    "name_ru",
    "name_kk",
    "name_en",
    "source_reference",
}


def load_bootstrap(path: Path = BOOTSTRAP_PATH) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    terms = payload.get("terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("controlled vocabulary bootstrap must contain non-empty terms")

    seen: set[tuple[VocabularyCode, str]] = set()
    result: list[dict] = []
    for index, item in enumerate(terms):
        if not isinstance(item, dict):
            raise ValueError(f"term #{index} must be an object")
        missing = _REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"term #{index} is missing fields: {sorted(missing)}")

        vocabulary = VocabularyCode(item["vocabulary"])
        code = str(item["code"]).strip()
        if not code:
            raise ValueError(f"term #{index} has empty code")
        key = (vocabulary, code)
        if key in seen:
            raise ValueError(f"duplicate controlled vocabulary term: {vocabulary.value}/{code}")
        seen.add(key)

        result.append(
            {
                "vocabulary": vocabulary,
                "code": code,
                "name_ru": str(item["name_ru"]).strip(),
                "name_kk": str(item["name_kk"]).strip(),
                "name_en": str(item["name_en"]).strip(),
                "aliases": list(item.get("aliases", [])),
                "description": item.get("description"),
                "source_reference": str(item["source_reference"]).strip(),
                "metadata_payload": dict(item.get("metadata", {})),
                "is_active": bool(item.get("is_active", True)),
            }
        )
    return result


async def seed() -> tuple[int, int]:
    created = 0
    updated = 0
    terms = load_bootstrap()

    async with AsyncSessionFactory() as session:
        for values in terms:
            existing = await session.scalar(
                select(ControlledVocabularyTerm).where(
                    ControlledVocabularyTerm.vocabulary == values["vocabulary"],
                    ControlledVocabularyTerm.code == values["code"],
                )
            )
            if existing is None:
                session.add(ControlledVocabularyTerm(**values))
                created += 1
                continue

            for field, value in values.items():
                setattr(existing, field, value)
            updated += 1

        await session.commit()

    return created, updated


async def main() -> None:
    created, updated = await seed()
    print(f"Controlled vocabularies seeded: created={created}, updated={updated}")


if __name__ == "__main__":
    asyncio.run(main())
