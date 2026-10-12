"""Shared helpers used by more than one product service."""

import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.category.models.category import CategoryModel
from apps.product.models.product import ProductModel
from apps.product.schemas.response import ProductListItemResponse, ProductPageResponse
from core.types import ProductStatusType


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


async def build_product_page(
    session: AsyncSession,
    items: list[ProductModel],
    total: int,
    page: int,
    limit: int,
) -> ProductPageResponse:
    """Build a ProductPageResponse from a list of product models.

    Args:
        session: Async database session.
        items: List of ProductModel instances.
        total: Total count of matching products.
        page: Current page number.
        limit: Page size.

    Returns:
        Fully populated ProductPageResponse.
    """
    # Batch-resolve categories for all items
    category_ids = list({item.category_id for item in items if item.category_id})
    categories_map = await resolve_categories(session, category_ids)

    list_items = [
        ProductListItemResponse(
            id=p.id,
            sku=p.sku,
            name=p.name,
            unit=p.unit.value,
            price=p.price,
            stock=p.stock,
            reorderLevel=p.reorder_level,
            status=p.status.value,
            categoryId=p.category_id,
            categoryName=categories_map.get(p.category_id).name if p.category_id in categories_map else None,
            createdAt=p.created_at,
        )
        for p in items
    ]

    pages = math.ceil(total / limit) if limit > 0 else 0

    return ProductPageResponse(
        items=list_items,
        meta={
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        },
    )
