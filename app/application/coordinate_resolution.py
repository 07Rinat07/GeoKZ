from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.coordinates import CoordinateResolver
from app.application.crs_registry import OrganizationCrsRegistryService
from app.application.errors import CrsDefinitionValidationError
from app.schemas.coordinates import (
    CoordinateInput,
    ProjectedAxisOrder,
    ProjectedCoordinateInput,
    ResolvedCoordinate,
)


@dataclass(slots=True)
class CoordinateResolutionService:
    session: AsyncSession

    async def resolve(self, coordinate: CoordinateInput) -> ResolvedCoordinate:
        if not isinstance(coordinate, ProjectedCoordinateInput):
            return CoordinateResolver().resolve(coordinate)

        if coordinate.registered_crs_code is None:
            return CoordinateResolver().resolve(coordinate)

        definition = await OrganizationCrsRegistryService(self.session).get_resolvable(
            coordinate.registered_crs_code
        )
        registered_axis_order = ProjectedAxisOrder(definition.default_axis_order)
        if (
            coordinate.axis_order is not None
            and coordinate.axis_order != registered_axis_order
        ):
            raise CrsDefinitionValidationError(
                "The supplied axis_order differs from the confirmed registered CRS axis order."
            )

        raw_coordinate = ProjectedCoordinateInput(
            x=coordinate.x,
            y=coordinate.y,
            crs=definition.definition,
            axis_order=registered_axis_order,
        )
        resolved = CoordinateResolver().resolve(raw_coordinate)
        return resolved.model_copy(
            update={"registered_crs_code": definition.code}
        )
