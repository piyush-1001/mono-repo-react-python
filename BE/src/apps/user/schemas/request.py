"""User request schemas."""

from typing import Annotated
from uuid import UUID

from core.types import RoleType
from core.utils.schema import CamelCaseModel

from apps.user.types import UserSortField


class EncryptedRequest(CamelCaseModel):
    """RSA-encrypted request body used by auth endpoints."""

    encryptedData: str
    encryptedKey: str
    iv: str


class LoginUserRequest(CamelCaseModel):
    """Sign-in payload after RSA decryption."""

    email: str
    password: str


class CreateUserRequest(CamelCaseModel):
    """Create a new user account."""

    firstName: str
    lastName: str
    email: str
    password: str
    phone: str | None = None
    role: RoleType = RoleType.USER


class UpdateUserRequest(CamelCaseModel):
    """Full replace of user editable fields (PUT)."""

    firstName: str
    lastName: str
    email: str
    phone: str | None = None
    role: RoleType
    isActive: bool


class PatchUserStatusRequest(CamelCaseModel):
    """Targeted status update (PATCH /{user_id})."""

    isActive: bool


class GetUserByIdRequest(CamelCaseModel):
    """Query schema for fetching a single user by UUID."""

    userId: UUID


class ListUsersRequest(CamelCaseModel):
    """Query schema for the user list endpoint."""

    search: str | None = None
    role: RoleType | None = None
    page: Annotated[int, lambda x: x if x > 0 else 1] = 1
    limit: Annotated[int, lambda x: min(max(x, 1), 100)] = 20
    sort: UserSortField = UserSortField.CREATED_AT
