from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.application.audit import AuditActor, AuditRevisionService
from app.core.config import get_settings
from app.core.security import hash_password, hash_token, issue_opaque_token, verify_password
from app.models.auth import AuthSession, UserAccount
from app.models.enums import AuditAction, UserRole


class AuthenticationError(ValueError):
    pass


class UserAccountConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LoginResult:
    token: str
    session: AuthSession
    user: UserAccount


@dataclass(slots=True)
class AuthenticationService:
    session: AsyncSession

    async def create_user(
        self,
        *,
        username: str,
        display_name: str,
        role: UserRole,
        password: str,
        created_by: UserAccount | None = None,
    ) -> UserAccount:
        normalized_username = username.strip().lower()
        user = UserAccount(
            username=normalized_username,
            display_name=display_name.strip(),
            role=role,
            password_hash=hash_password(password),
            is_active=True,
        )
        self.session.add(user)
        try:
            await self.session.flush()
            actor = AuditActor.from_user(created_by or user)
            await AuditRevisionService(self.session).append_audit(
                actor=actor,
                action=AuditAction.CREATE,
                resource_type="user_account",
                resource_id=user.id,
                reason="bootstrap" if created_by is None else "admin_create_user",
                details={"username": user.username, "role": user.role.value},
            )
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise UserAccountConflictError("User account already exists") from error
        await self.session.refresh(user)
        return user

    async def login(self, *, username: str, password: str) -> LoginResult:
        normalized_username = username.strip().lower()
        user = await self.session.scalar(
            select(UserAccount).where(UserAccount.username == normalized_username)
        )
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password")

        now = datetime.now(UTC)
        settings = get_settings()
        token = issue_opaque_token()
        auth_session = AuthSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=now + timedelta(hours=settings.auth_session_hours),
            last_used_at=now,
        )
        user.last_login_at = now
        self.session.add(auth_session)
        await AuditRevisionService(self.session).append_audit(
            actor=AuditActor.from_user(user),
            action=AuditAction.LOGIN,
            resource_type="auth_session",
            resource_id=auth_session.id,
            details={"expires_at": auth_session.expires_at},
        )
        await self.session.commit()
        await self.session.refresh(auth_session)
        return LoginResult(token=token, session=auth_session, user=user)

    async def authenticate_token(self, token: str) -> tuple[AuthSession, UserAccount]:
        now = datetime.now(UTC)
        auth_session = await self.session.scalar(
            select(AuthSession)
            .options(joinedload(AuthSession.user))
            .where(AuthSession.token_hash == hash_token(token))
        )
        if (
            auth_session is None
            or auth_session.revoked_at is not None
            or auth_session.expires_at <= now
            or not auth_session.user.is_active
        ):
            raise AuthenticationError("Authentication session is invalid or expired")
        return auth_session, auth_session.user

    async def logout(self, *, token: str) -> None:
        auth_session, user = await self.authenticate_token(token)
        auth_session.revoked_at = datetime.now(UTC)
        await AuditRevisionService(self.session).append_audit(
            actor=AuditActor.from_user(user),
            action=AuditAction.LOGOUT,
            resource_type="auth_session",
            resource_id=auth_session.id,
        )
        await self.session.commit()
