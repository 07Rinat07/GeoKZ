import asyncio
from decimal import Decimal
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.correlation import WellMarker
from app.models.entity import GeologicalEntity
from app.models.enums import (
    DepthReference,
    FluidType,
    HydrocarbonStatus,
    VerificationStatus,
    WellType,
)
from app.models.well import Well, WellInterval

DEMO_TAG = "synthetic-correlation-demo-v1"


async def get_or_create_entity(session, **values: Any) -> GeologicalEntity:
    existing = await session.scalar(
        select(GeologicalEntity).where(
            GeologicalEntity.external_id == values["external_id"]
        )
    )
    if existing is not None:
        return existing
    entity = GeologicalEntity(**values)
    session.add(entity)
    await session.flush()
    return entity


async def get_or_create_well(session, **values: Any) -> Well:
    existing = await session.scalar(
        select(Well).where(Well.external_id == values["external_id"])
    )
    if existing is not None:
        return existing
    well = Well(**values)
    session.add(well)
    await session.flush()
    return well


async def get_or_create_marker(session, **values: Any) -> WellMarker:
    existing = await session.scalar(
        select(WellMarker).where(
            WellMarker.well_id == values["well_id"],
            WellMarker.marker_code == values["marker_code"],
        )
    )
    if existing is not None:
        return existing
    marker = WellMarker(**values)
    session.add(marker)
    await session.flush()
    return marker


async def get_or_create_interval(session, **values: Any) -> WellInterval:
    existing = await session.scalar(
        select(WellInterval).where(
            WellInterval.external_id == values["external_id"]
        )
    )
    if existing is not None:
        return existing
    interval = WellInterval(**values)
    session.add(interval)
    await session.flush()
    return interval


async def seed() -> None:
    async with AsyncSessionFactory() as session:
        field = await get_or_create_entity(
            session,
            external_id="demo-mangystau-correlation-field",
            object_type="field",
            name_ru="[DEMO] Корреляционное месторождение",
            name_kk="[DEMO] Корреляциялық кен орны",
            name_en="[DEMO] Correlation Field",
            geological_context={
                "dataset": DEMO_TAG,
                "synthetic": True,
                "warning_ru": "Учебные синтетические данные. Не использовать как производственные факты.",
                "warning_kk": "Оқу үшін синтетикалық деректер. Өндірістік факт ретінде қолданбаңыз.",
                "warning_en": "Synthetic training data. Do not use as production facts.",
            },
            verification_status=VerificationStatus.DRAFT,
        )

        well_specs = [
            ("01", 51.168420, 43.652341, Decimal("3200")),
            ("02", 51.180000, 43.652341, Decimal("3250")),
            ("03", 51.158000, 43.660000, Decimal("3180")),
            ("04", 51.190000, 43.660000, Decimal("3300")),
        ]
        marker_depths = {
            "01": {"R1": Decimal("2451.6"), "R2": Decimal("2520.0")},
            "02": {"R1": Decimal("2470.0"), "R2": Decimal("2535.0")},
            "03": {"R1": Decimal("2438.0"), "R2": Decimal("2510.0")},
            "04": {"R1": Decimal("2462.0"), "R2": Decimal("2528.5")},
        }
        reservoir_specs = {
            "01": ("2450", "2478", "18.2", "17.4", "124", ["sandstone"], FluidType.OIL, HydrocarbonStatus.TESTED_FLOW),
            "02": ("2471", "2492", "12.7", "15.8", "83", ["sandstone", "siltstone"], FluidType.MIXED, HydrocarbonStatus.LOG_INTERPRETATION),
            "03": ("2436", "2469", "21.1", "18.1", "148", ["sandstone"], FluidType.OIL, HydrocarbonStatus.TESTED_FLOW),
            "04": ("2460", "2485", "9.4", "14.9", "61", ["siltstone", "sandstone"], FluidType.WATER, HydrocarbonStatus.NEGATIVE),
        }

        for code, longitude, latitude, total_depth in well_specs:
            well_entity = await get_or_create_entity(
                session,
                external_id=f"demo-correlation-well-entity-{code}",
                object_type="well",
                parent_id=field.id,
                name_ru=f"[DEMO] Скважина {code}",
                name_kk=f"[DEMO] Ұңғыма {code}",
                name_en=f"[DEMO] Well {code}",
                geological_context={"dataset": DEMO_TAG, "synthetic": True},
                verification_status=VerificationStatus.DRAFT,
            )
            well = await get_or_create_well(
                session,
                external_id=f"demo-correlation-well-{code}",
                entity_id=well_entity.id,
                object_entity_id=field.id,
                name=f"DEMO-AKT-{code}",
                aliases=[],
                well_type=WellType.EXPLORATION,
                total_depth_m=total_depth,
                location=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
                source_ids=[DEMO_TAG],
                verification_status=VerificationStatus.DRAFT,
            )

            for marker_code, depth in marker_depths[code].items():
                await get_or_create_marker(
                    session,
                    well_id=well.id,
                    marker_code=marker_code,
                    marker_type="stratigraphic",
                    name_ru=f"[DEMO] Репер {marker_code}",
                    name_kk=f"[DEMO] {marker_code} репері",
                    name_en=f"[DEMO] Marker {marker_code}",
                    depth_m=depth,
                    depth_reference=DepthReference.TVDSS,
                    tvdss_m=depth,
                    interpretation_method="synthetic_demo",
                    confidence_percent=Decimal("90"),
                    notes="Synthetic demo marker; not a production geological fact.",
                    verification_status=VerificationStatus.DRAFT,
                )

            top, base, net_pay, porosity, permeability, lithologies, fluid, hc_status = (
                reservoir_specs[code]
            )
            await get_or_create_interval(
                session,
                external_id=f"demo-correlation-well-{code}-j2",
                well_id=well.id,
                top_depth_m=Decimal(top),
                base_depth_m=Decimal(base),
                depth_reference=DepthReference.TVDSS,
                local_horizon="J-II",
                lithologies=lithologies,
                porosity_percent=Decimal(porosity),
                permeability_md=Decimal(permeability),
                net_pay_m=Decimal(net_pay),
                fluid_type=fluid,
                hydrocarbon_status=hc_status,
                source_ids=[DEMO_TAG],
                verification_status=VerificationStatus.DRAFT,
            )

        await session.commit()
        print(
            "Синтетический demo-набор корреляции добавлен: 4 скважины, "
            "реперы R1/R2 и горизонт J-II."
        )
        print("Важно: данные учебные и не являются реальными производственными фактами.")


if __name__ == "__main__":
    asyncio.run(seed())
