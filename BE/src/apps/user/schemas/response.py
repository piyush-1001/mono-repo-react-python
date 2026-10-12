"""User response schemas."""

from datetime import datetime
from typing import Annotated

from core.types import RoleType
from core.utils.schema import CamelCaseModel, PageMeta


class TokenPairResponse(CamelCaseModel):
    """Access and refresh token pair returned on sign-in and refresh."""

    accessToken: str
    refreshToken: str


class BaseUserResponse(CamelCaseModel):
    """Core user fields shared across multiple response shapes."""

    id: UUID
    firstName: str
    lastName: str
    email: str
    phone: str | None = None
    role: RoleType
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class CreateUserResponse(CamelCaseModel):
    """Lightweight response returned immediately after user creation."""

    id: UUID
    email: str
    createdAt: datetime


class UserListItemResponse(CamelCaseModel):
    """User record as it appears inside a paginated list."""

    id: UUID
    firstName: str
    lastName: str
    email: str
    phone: str | None = None
    role: RoleType
    isActive: bool
    createdAt: datetime


class UserPageResponse(CamelCaseModel):
    """Paginated list of users with metadata."""

    items: list[UserListItemResponse]
    meta: PageMeta


class CurrentUserResponse(BaseUserResponse):
    """Full user record including last login and creator info."""

    lastLoginAt: datetime | None = None
    createdBy: UUID | None = None
