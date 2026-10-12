"""Shared helpers used by multiple user services."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from apps.user.models.user import UserModel


async def fetch_user(session: AsyncSession, user_id: UUID) -> "UserModel | None":
    """Fetch a user by UUID.

    Args:
        session: Async database session.
        user_id: UUID of the user to fetch.

    Returns:
        UserModel instance or None if not found.
    """
    return await session.scalar(
        select(UserModel).where(UserModel.id == user_id)
    )


async def verify_active_user(session: AsyncSession, user_id: UUID) -> "UserModel":
    """Fetch an active user or raise.

    Args:
        session: Async database session.
        user_id: UUID of the user.

    Returns:
        Active UserModel instance.

    Raises:
        UserNotFoundException: When the user does not exist.
        InactiveUserException: When the user is deactivated.
    """
    from apps.user.exceptions import InactiveUserException, UserNotFoundException

    user = await fetch_user(session, user_id)
    if user is None:
        raise UserNotFoundException
    if not user.is_active:
        raise InactiveUserException
    return user


def build_user_page(
    total: int,
    page: int,
    limit: int,
) -> dict[str, int]:
    """Compute pagination metadata for a user list response.

    Args:
        total: Total number of matching records.
        page: Current page number (1-indexed).
        limit: Page size.

    Returns:
        Dict with ``total``, ``page``, ``limit``, and ``pages`` keys.
    """
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return {"total": total, "page": page, "limit": limit, "pages": pages}
