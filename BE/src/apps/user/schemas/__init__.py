"""User feature schemas."""

# --- Requests ---
from apps.user.schemas.request import (
    CreateUserRequest,
    EncryptedRequest,
    GetUserByIdRequest,
    ListUsersRequest,
    LoginUserRequest,
    PatchUserStatusRequest,
    UpdateUserRequest,
)

# --- Responses ---
from apps.user.schemas.response import (
    BaseUserResponse,
    CreateUserResponse,
    CurrentUserResponse,
    TokenPairResponse,
    UserListItemResponse,
    UserPageResponse,
)

__all__ = [
    # Requests
    "CreateUserRequest",
    "EncryptedRequest",
    "GetUserByIdRequest",
    "ListUsersRequest",
    "LoginUserRequest",
    "PatchUserStatusRequest",
    "UpdateUserRequest",
    # Responses
    "BaseUserResponse",
    "CreateUserResponse",
    "CurrentUserResponse",
    "TokenPairResponse",
    "UserListItemResponse",
    "UserPageResponse",
]
