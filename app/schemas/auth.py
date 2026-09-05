from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=12, max_length=256)


class AuthenticatedUserRead(BaseModel):
    id: UUID
    username: str
    display_name: str
    role: UserRole
    is_active: bool


class LoginResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    expires_at: datetime
    user: AuthenticatedUserRead


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=120, pattern=r"^[a-zA-Z0-9._-]+$")
    display_name: str = Field(min_length=2, max_length=200)
    role: UserRole
    password: str = Field(min_length=12, max_length=256)


class UserAccountRead(AuthenticatedUserRead):
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
