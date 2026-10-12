"""User feature types and enums."""

from enum import StrEnum

from core.types import RoleType


class UserSortField(StrEnum):
    """Fields available for user list ordering."""

    CREATED_AT = "created_at"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
