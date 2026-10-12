"""Category service."""

import math
from typing import Annotated

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.category.exceptions import (
    CategoryCodeExistsException,
    CategoryNotEmptyException,
    CategoryNotFoundException,
)
from apps.category.models.category import CategoryModel
from apps.category.schemas.request import (
    CreateCategoryRequest,
    ListCategoriesRequest,
    UpdateCategoryRequest,
)
from apps.category.schemas.response import (
    CategoryListItemResponse,
    CategoryPageResponse,
    CategoryResponse,
)
from constants import category_code_re
from core.common_helpers import validate_input_fields
from core.db import db_session


class CategoryService:
    """Service for managing product categories."""

    def __init__(self, session: Annotated[AsyncSession, db_session]) -> None:
        """Initialize category service.

        Args:
            session: Async database session.
        """
        self.session = session

    async def list_categories(
        self,
        search: str | None,
        is_active: bool | None,
        page: int,
        limit: int,
    ) -> CategoryPageResponse:
        """List categories with pagination and optional filters.

        Args:
            search: Optional name/code search term.
            is_active: Optional filter by active status.
            page: Page number (1-indexed).
            limit: Number of items per page.

        Returns:
            Paginated list of categories with product counts.
        """
        query = select(CategoryModel)
        count_query = select(func.count(CategoryModel.id))

        if search:
            term = f"%{search}%"
            query = query.where(
                (CategoryModel.name.ilike(term)) | (CategoryModel.code.ilike(term))
            )
            count_query = count_query.where(
                (CategoryModel.name.ilike(term)) | (CategoryModel.code.ilike(term))
            )

        if is_active is not None:
            query = query.where(CategoryModel.is_active == is_active)
            count_query = count_query.where(CategoryModel.is_active == is_active)

        total = await self.session.scalar(count_query) or 0

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit).order_by(CategoryModel.name)
        categories = await self.session.scalars(query)

        # Build product count subquery
        from apps.product.models.product import ProductModel

        count_sub = (
            select(func.count(ProductModel.id))
            .where(ProductModel.category_id == CategoryModel.id)
            .correlate(CategoryModel)
            .scalar_subquery()
        )
        items_query = (
            select(CategoryModel, count_sub.label("product_count"))
            .options()
            .where(CategoryModel.id.in_([c.id for c in categories]))
        )

        rows = await self.session.execute(items_query)
        items = [
            CategoryListItemResponse(
                id=row[0].id,
                name=row[0].name,
                code=row[0].code,
                isActive=row[0].is_active,
                productCount=row[1] or 0,
            )
            for row in rows.all()
        ]

        if not items:
            items = [
                CategoryListItemResponse(
                    id=c.id,
                    name=c.name,
                    code=c.code,
                    isActive=c.is_active,
                    productCount=0,
                )
                for c in categories
            ]

        pages = math.ceil(total / limit) if limit > 0 else 0

        return CategoryPageResponse(
            items=items,
            meta={
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
            },
        )

    async def get_category_by_id(self, category_id) -> CategoryResponse:
        """Fetch a single category by ID.

        Args:
            category_id: UUID of the category.

        Returns:
            Category response schema.

        Raises:
            CategoryNotFoundException: When the category does not exist.
        """
        category = await self.session.scalar(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        if not category:
            raise CategoryNotFoundException
        return CategoryResponse.model_validate(category)

    async def create_category(
        self,
        name: str,
        code: str,
        description: str | None,
        is_active: bool,
    ) -> CategoryResponse:
        """Create a new category.

        Args:
            name: Category display name.
            code: Unique category code.
            description: Optional description.
            is_active: Whether the category is active.

        Returns:
            Created category response.

        Raises:
            CategoryCodeExistsException: When the code is already taken.
        """
        validate_input_fields(name=name, code=code)

        if not category_code_re.match(code):
            from core.exceptions import UnprocessableEntityError
            raise UnprocessableEntityError(message="Invalid category code format")

        existing = await self.session.scalar(
            select(CategoryModel).where(CategoryModel.code == code)
        )
        if existing:
            raise CategoryCodeExistsException

        category = CategoryModel.create(
            name=name,
            code=code,
            description=description,
            is_active=is_active,
        )
        self.session.add(category)
        return CategoryResponse.model_validate(category)

    async def update_category(
        self,
        category_id,
        name: str | None,
        description: str | None,
        is_active: bool | None,
    ) -> CategoryResponse:
        """Update an existing category.

        Args:
            category_id: UUID of the category to update.
            name: New display name, or None to leave unchanged.
            description: New description, or None to leave unchanged.
            is_active: New active flag, or None to leave unchanged.

        Returns:
            Updated category response.

        Raises:
            CategoryNotFoundException: When the category does not exist.
        """
        category = await self.session.scalar(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        if not category:
            raise CategoryNotFoundException

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if is_active is not None:
            category.is_active = is_active

        return CategoryResponse.model_validate(category)

    async def delete_category(self, category_id) -> None:
        """Delete a category after verifying it has no products.

        Args:
            category_id: UUID of the category to delete.

        Raises:
            CategoryNotFoundException: When the category does not exist.
            CategoryNotEmptyException: When the category still has products.
        """
        from apps.product.models.product import ProductModel

        category = await self.session.scalar(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        if not category:
            raise CategoryNotFoundException

        product_count = await self.session.scalar(
            select(func.count(ProductModel.id)).where(
                ProductModel.category_id == category_id
            )
        )
        if product_count and product_count > 0:
            raise CategoryNotEmptyException

        await self.session.delete(category)
        await self.session.commit()
