from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pyproj import CRS
from pyproj.exceptions import CRSError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import (
    CrsDefinitionConflictError,
    CrsDefinitionNotConfirmedError,
    CrsDefinitionNotFoundError,
    CrsDefinitionValidationError,
)
from app.core.project_info import SupportedLanguage
from app.models.crs import OrganizationCrsDefinition
from app.schemas.coordinates import ProjectedAxisOrder
from app.schemas.crs import (
    CrsDefinitionKind,
    OrganizationCrsDefinitionConfirm,
    OrganizationCrsDefinitionCreate,
    OrganizationCrsDefinitionListResponse,
    OrganizationCrsDefinitionResponse,
    OrganizationCrsDefinitionUpdate,
)


@dataclass(frozen=True, slots=True)
class ValidatedCrsDefinition:
    definition: str
    canonical_wkt: str
    authority_name: str | None
    authority_code: str | None


def validate_crs_definition(
    definition_kind: CrsDefinitionKind,
    definition: str,
) -> ValidatedCrsDefinition:
    value = definition.strip()
    try:
        if definition_kind == CrsDefinitionKind.EPSG:
            code_text = value.upper()
            if code_text.startswith("EPSG:"):
                code_text = code_text[5:]
            try:
                epsg = int(code_text)
            except ValueError as error:
                raise CrsDefinitionValidationError(
                    "EPSG definition must be an integer code or EPSG:<code>."
                ) from error
            crs = CRS.from_epsg(epsg)
            normalized_definition = f"EPSG:{epsg}"
        elif definition_kind == CrsDefinitionKind.WKT:
            crs = CRS.from_wkt(value)
            normalized_definition = value
        else:
            if "+proj=" not in value and "proj=" not in value:
                raise CrsDefinitionValidationError(
                    "PROJ definition must contain an explicit proj parameter."
                )
            crs = CRS.from_user_input(value)
            normalized_definition = value
    except CRSError as error:
        raise CrsDefinitionValidationError(
            "The CRS definition cannot be parsed by PROJ/pyproj."
        ) from error

    if not crs.is_projected:
        raise CrsDefinitionValidationError(
            "Organization CRS definitions used for X/Y must be projected coordinate systems."
        )

    authority = crs.to_authority()
    return ValidatedCrsDefinition(
        definition=normalized_definition,
        canonical_wkt=crs.to_wkt(version="WKT2_2019", pretty=False),
        authority_name=authority[0] if authority else None,
        authority_code=authority[1] if authority else None,
    )


def _localized_name(
    definition: OrganizationCrsDefinition,
    language: SupportedLanguage,
) -> str:
    return {
        "ru": definition.name_ru,
        "kk": definition.name_kk,
        "en": definition.name_en,
    }[language]


def _to_response(
    definition: OrganizationCrsDefinition,
    language: SupportedLanguage,
) -> OrganizationCrsDefinitionResponse:
    return OrganizationCrsDefinitionResponse(
        id=definition.id,
        code=definition.code,
        name_ru=definition.name_ru,
        name_kk=definition.name_kk,
        name_en=definition.name_en,
        display_name=_localized_name(definition, language),
        language=language,
        definition_kind=CrsDefinitionKind(definition.definition_kind),
        definition=definition.definition,
        canonical_wkt=definition.canonical_wkt,
        authority_name=definition.authority_name,
        authority_code=definition.authority_code,
        default_axis_order=ProjectedAxisOrder(definition.default_axis_order),
        source_reference=definition.source_reference,
        notes=definition.notes,
        is_confirmed=definition.is_confirmed,
        confirmed_by=definition.confirmed_by,
        confirmed_at=definition.confirmed_at,
        confirmation_note=definition.confirmation_note,
        is_active=definition.is_active,
        selectable=definition.is_active and definition.is_confirmed,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
    )


@dataclass(slots=True)
class OrganizationCrsRegistryService:
    session: AsyncSession

    async def list(
        self,
        *,
        language: SupportedLanguage,
        selectable_only: bool = False,
    ) -> OrganizationCrsDefinitionListResponse:
        statement = select(OrganizationCrsDefinition)
        if selectable_only:
            statement = statement.where(
                OrganizationCrsDefinition.is_active.is_(True),
                OrganizationCrsDefinition.is_confirmed.is_(True),
            )
        definitions = list(
            await self.session.scalars(statement.order_by(OrganizationCrsDefinition.code))
        )
        return OrganizationCrsDefinitionListResponse(
            language=language,
            items=[_to_response(item, language) for item in definitions],
        )

    async def create(
        self,
        payload: OrganizationCrsDefinitionCreate,
        *,
        language: SupportedLanguage,
    ) -> OrganizationCrsDefinitionResponse:
        validated = validate_crs_definition(
            payload.definition_kind,
            payload.definition,
        )
        definition = OrganizationCrsDefinition(
            code=payload.code.lower(),
            name_ru=payload.name_ru,
            name_kk=payload.name_kk,
            name_en=payload.name_en,
            definition_kind=payload.definition_kind.value,
            definition=validated.definition,
            canonical_wkt=validated.canonical_wkt,
            authority_name=validated.authority_name,
            authority_code=validated.authority_code,
            default_axis_order=payload.default_axis_order.value,
            source_reference=payload.source_reference,
            notes=payload.notes,
            is_confirmed=False,
            is_active=True,
        )
        self.session.add(definition)
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise CrsDefinitionConflictError(
                f"CRS definition code '{payload.code.lower()}' already exists."
            ) from error
        await self.session.refresh(definition)
        return _to_response(definition, language)

    async def update(
        self,
        definition_id: UUID,
        payload: OrganizationCrsDefinitionUpdate,
        *,
        language: SupportedLanguage,
    ) -> OrganizationCrsDefinitionResponse:
        definition = await self._get(definition_id)
        fields = payload.model_fields_set

        if "name_ru" in fields and payload.name_ru is not None:
            definition.name_ru = payload.name_ru
        if "name_kk" in fields and payload.name_kk is not None:
            definition.name_kk = payload.name_kk
        if "name_en" in fields and payload.name_en is not None:
            definition.name_en = payload.name_en
        if "notes" in fields:
            definition.notes = payload.notes
        if "is_active" in fields and payload.is_active is not None:
            definition.is_active = payload.is_active

        confirmation_sensitive_change = False
        if "definition_kind" in fields or "definition" in fields:
            definition_kind = (
                payload.definition_kind
                if payload.definition_kind is not None
                else CrsDefinitionKind(definition.definition_kind)
            )
            definition_text = (
                payload.definition
                if payload.definition is not None
                else definition.definition
            )
            validated = validate_crs_definition(definition_kind, definition_text)
            definition.definition_kind = definition_kind.value
            definition.definition = validated.definition
            definition.canonical_wkt = validated.canonical_wkt
            definition.authority_name = validated.authority_name
            definition.authority_code = validated.authority_code
            confirmation_sensitive_change = True

        if "default_axis_order" in fields and payload.default_axis_order is not None:
            definition.default_axis_order = payload.default_axis_order.value
            confirmation_sensitive_change = True

        if "source_reference" in fields and payload.source_reference is not None:
            definition.source_reference = payload.source_reference
            confirmation_sensitive_change = True

        if confirmation_sensitive_change:
            self._reset_confirmation(definition)

        await self.session.commit()
        await self.session.refresh(definition)
        return _to_response(definition, language)

    async def confirm(
        self,
        definition_id: UUID,
        payload: OrganizationCrsDefinitionConfirm,
        *,
        language: SupportedLanguage,
    ) -> OrganizationCrsDefinitionResponse:
        definition = await self._get(definition_id)
        if not definition.source_reference.strip():
            raise CrsDefinitionValidationError(
                "A source reference is required before confirming an organization CRS."
            )

        validated = validate_crs_definition(
            CrsDefinitionKind(definition.definition_kind),
            definition.definition,
        )
        definition.definition = validated.definition
        definition.canonical_wkt = validated.canonical_wkt
        definition.authority_name = validated.authority_name
        definition.authority_code = validated.authority_code
        definition.is_confirmed = True
        definition.confirmed_by = payload.confirmed_by
        definition.confirmed_at = datetime.now(UTC)
        definition.confirmation_note = payload.confirmation_note

        await self.session.commit()
        await self.session.refresh(definition)
        return _to_response(definition, language)

    async def get_resolvable(self, code: str) -> OrganizationCrsDefinition:
        definition = await self.session.scalar(
            select(OrganizationCrsDefinition).where(
                OrganizationCrsDefinition.code == code.lower()
            )
        )
        if definition is None:
            raise CrsDefinitionNotFoundError(
                f"Registered CRS definition '{code}' was not found."
            )
        if not definition.is_active:
            raise CrsDefinitionNotConfirmedError(
                f"Registered CRS definition '{code}' is inactive."
            )
        if not definition.is_confirmed:
            raise CrsDefinitionNotConfirmedError(
                f"Registered CRS definition '{code}' has not been confirmed."
            )
        return definition

    async def _get(self, definition_id: UUID) -> OrganizationCrsDefinition:
        definition = await self.session.get(OrganizationCrsDefinition, definition_id)
        if definition is None:
            raise CrsDefinitionNotFoundError(
                f"Organization CRS definition '{definition_id}' was not found."
            )
        return definition

    @staticmethod
    def _reset_confirmation(definition: OrganizationCrsDefinition) -> None:
        definition.is_confirmed = False
        definition.confirmed_by = None
        definition.confirmed_at = None
        definition.confirmation_note = None
