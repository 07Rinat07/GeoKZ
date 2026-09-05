from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_dependencies import (
    CurrentPrincipal,
    get_current_principal,
    require_admin,
)
from app.application.auth import (
    AuthenticationError,
    AuthenticationService,
    UserAccountConflictError,
)
from app.core.database import get_session
from app.models.auth import UserAccount
from app.schemas.auth import (
    AuthenticatedUserRead,
    CreateUserRequest,
    LoginRequest,
    LoginResponse,
    UserAccountRead,
)

router = APIRouter()


def _user_read(user: UserAccount) -> AuthenticatedUserRead:
    return AuthenticatedUserRead(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    try:
        result = await AuthenticationService(session).login(
            username=payload.username,
            password=payload.password,
        )
    except AuthenticationError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    return LoginResponse(
        access_token=result.token,
        expires_at=result.session.expires_at,
        user=_user_read(result.user),
    )


@router.get("/me", response_model=AuthenticatedUserRead)
async def me(
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> AuthenticatedUserRead:
    return _user_read(principal.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> None:
    await AuthenticationService(session).logout(token=principal.token)


@router.post("/users", response_model=UserAccountRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    principal: CurrentPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> UserAccount:
    try:
        return await AuthenticationService(session).create_user(
            username=payload.username,
            display_name=payload.display_name,
            role=payload.role,
            password=payload.password,
            created_by=principal.user,
        )
    except UserAccountConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/users", response_model=list[UserAccountRead])
async def list_users(
    _principal: CurrentPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[UserAccount]:
    return list(await session.scalars(select(UserAccount).order_by(UserAccount.username)))
