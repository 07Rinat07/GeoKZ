from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth import AuthenticationError, AuthenticationService
from app.core.database import get_session
from app.models.auth import AuthSession, UserAccount
from app.models.enums import UserRole

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentPrincipal:
    token: str
    auth_session: AuthSession
    user: UserAccount


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> CurrentPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        auth_session, user = await AuthenticationService(session).authenticate_token(
            credentials.credentials
        )
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return CurrentPrincipal(
        token=credentials.credentials,
        auth_session=auth_session,
        user=user,
    )


def require_roles(*roles: UserRole) -> Callable[..., CurrentPrincipal]:
    allowed = set(roles)

    async def dependency(
        principal: CurrentPrincipal = Depends(get_current_principal),
    ) -> CurrentPrincipal:
        if principal.user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this operation",
            )
        return principal

    return dependency


require_expert = require_roles(UserRole.EXPERT, UserRole.ADMIN)
require_editor = require_roles(UserRole.EDITOR, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)
require_scientific_writer = require_roles(UserRole.EXPERT, UserRole.EDITOR, UserRole.ADMIN)
