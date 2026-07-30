import asyncio
from typing import Any

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.entity import GeologicalEntity
from app.models.enums import (
    AccessLevel,
    GeometryStatus,
    ReliabilityLevel,
    SourceDocumentType,
    VerificationStatus,
)
from app.models.source import Source

SOURCES: list[dict[str, Any]] = [
    {
        "external_id": "geology-ussr-vol21-west-kazakhstan-book1-1970",
        "title": "Геология СССР. Том XXI. Западный Казахстан. Часть I. Геологическое описание. Книга 1",
        "authors": ["Коллектив авторов"],
        "organization": "Министерство геологии СССР; Министерство геологии Казахской ССР",
        "publication_year": 1970,
        "survey_year_end": 1967,
        "document_type": SourceDocumentType.BOOK,
        "language": "ru",
        "territories": ["Западный Казахстан"],
        "objects": ["Прикаспийская впадина", "Мугоджары", "Устюрт", "Мангышлак"],
        "access_level": AccessLevel.LOCAL,
        "page_count": 880,
        "reliability_level": ReliabilityLevel.C,
        "notes": "Исторический региональный источник. Материалы учтены по состоянию на 01.01.1967.",
    },
    {
        "external_id": "geology-ussr-vol21-west-kazakhstan-book2-1970",
        "title": "Геология СССР. Том XXI. Западный Казахстан. Часть I. Геологическое описание. Книга 2",
        "authors": ["Коллектив авторов"],
        "organization": "Министерство геологии СССР; Министерство геологии Казахской ССР",
        "publication_year": 1970,
        "survey_year_end": 1967,
        "document_type": SourceDocumentType.BOOK,
        "language": "ru",
        "territories": ["Западный Казахстан"],
        "objects": ["Прикаспийская впадина", "Туранская плита", "Мугоджары"],
        "access_level": AccessLevel.LOCAL,
        "page_count": 344,
        "reliability_level": ReliabilityLevel.C,
        "notes": "Магматизм, метаморфизм, тектоника, геоморфология и история развития.",
    },
    {
        "external_id": "dauletaly-pre-eia-2017",
        "title": "Предварительная оценка воздействия на окружающую среду к технологической схеме разработки месторождения Даулеталы",
        "authors": [],
        "organization": "АО «КоЖаН»; ТОО «КазНИГРИ»",
        "publication_year": 2017,
        "document_type": SourceDocumentType.PROJECT,
        "language": "ru",
        "territories": ["Атырауская область", "Жылыойский район"],
        "objects": ["месторождение Даулеталы"],
        "access_level": AccessLevel.LOCAL,
        "page_count": 18,
        "reliability_level": ReliabilityLevel.C,
        "notes": "Проектный источник. Геологические факты подлежат сверке с первичными отчётами и актуальными данными.",
    },
]


async def get_or_create_source(session, values: dict[str, Any]) -> Source:
    existing = await session.scalar(
        select(Source).where(Source.external_id == values["external_id"])
    )
    if existing:
        return existing
    source = Source(**values)
    session.add(source)
    await session.flush()
    return source


async def get_or_create_entity(session, **values: Any) -> GeologicalEntity:
    existing = await session.scalar(
        select(GeologicalEntity).where(
            GeologicalEntity.external_id == values["external_id"]
        )
    )
    if existing:
        return existing
    entity = GeologicalEntity(**values)
    session.add(entity)
    await session.flush()
    return entity


async def seed() -> None:
    async with AsyncSessionFactory() as session:
        sources = [await get_or_create_source(session, values) for values in SOURCES]
        main_source = sources[1]
        dauletaly_source = sources[2]

        basin = await get_or_create_entity(
            session,
            external_id="kz-north-caspian-basin",
            object_type="sedimentary_basin",
            name_ru="Прикаспийская впадина",
            name_kk="Каспий маңы ойпаты",
            name_en="North Caspian Basin",
            geological_context={"province": "Восточно-Европейская платформа"},
            geometry_status=GeometryStatus.UNKNOWN,
            geometry_source_id=main_source.id,
            verification_status=VerificationStatus.REVIEWED,
        )
        uplift = await get_or_create_entity(
            session,
            external_id="kz-south-emba-uplift",
            object_type="uplift",
            parent_id=basin.id,
            name_ru="Южно-Эмбинское поднятие",
            name_en="South Emba Uplift",
            geological_context={"basin": "Прикаспийская впадина"},
            geometry_status=GeometryStatus.UNKNOWN,
            geometry_source_id=dauletaly_source.id,
            verification_status=VerificationStatus.DRAFT,
        )
        await get_or_create_entity(
            session,
            external_id="kz-atyrau-dauletaly-field",
            object_type="field",
            parent_id=uplift.id,
            name_ru="Даулеталы",
            name_en="Dauletaly",
            geological_context={
                "basin": "Прикаспийская впадина",
                "tectonic_zone": "Южно-Эмбинское поднятие",
                "structural_position": "солянокупольная структура",
            },
            geometry_status=GeometryStatus.UNKNOWN,
            geometry_source_id=dauletaly_source.id,
            verification_status=VerificationStatus.DRAFT,
        )

        await session.commit()
        print("Пилотные источники и объекты GeoKZ добавлены.")


if __name__ == "__main__":
    asyncio.run(seed())
