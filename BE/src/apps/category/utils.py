"""Shared helpers used by more than one category service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from apps.category.models.category import CategoryModel


async def resolve_categories(
    session: AsyncSession, category_ids: list[UUID]
) -> dict[UUID, CategoryModel]:
    """Fetch multiple categories by ID and return a lookup dict.

    Args:
        session: Async database session.
        category_ids: List of category UUIDs to resolve.

    Returns:
        Dictionary mapping category ID to CategoryModel instance.
    """
    if not category_ids:
        return {}

    result = await session.scalars(
        select(CategoryModel).where(CategoryModel.id.in_(category_ids))
    )
    return {cat.id: cat for cat in result.all()}
