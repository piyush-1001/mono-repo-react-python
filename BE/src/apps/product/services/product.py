"""Product service."""

import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from apps.category.models.category import CategoryModel
from apps.product.exceptions import (
    CategoryNotActiveException,
    ProductNotFoundException,
    SkuExistsException,
)
from apps.product.models.product import ProductModel
from apps.product.schemas.request import ListProductsRequest
from apps.product.schemas.response import (
    CreateProductResponse,
    ProductPageResponse,
    ProductResponse,
)
from apps.product.types import ProductSortField
from apps.product.utils import build_product_page
from constants import DEFAULT_PAGE_SIZE, LOW_STOCK_ALERT_BATCH, sku_re
from core.common_helpers import validate_input_fields
from core.db import db_session
from core.types import ProductStatusType

import constants


class ProductService:
    """Service for managing products."""

    def __init__(self, session: db_session) -> None:
        """Initialize product service.

        Args:
            session: Async database session.
        """
        self.session = session

    async def list_products(
        self,
        search: str | None,
        category_id: UUID | None,
        status: ProductStatusType | None,
        page: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> ProductPageResponse:
        """List products with filters, sorting, and pagination.

        Args:
            search: Optional name/SKU search term.
            category_id: Optional filter by category.
            status: Optional filter by product status.
            page: Page number (1-indexed).
            limit: Number of items per page.
            sort_by: Field to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Paginated list of products.
        """
        query = select(ProductModel)
        count_query = select(func.count(ProductModel.id))

        if search:
            term = f"%{search}%"
            query = query.where(
                (ProductModel.name.ilike(term)) | (ProductModel.sku.ilike(term))
            )
            count_query = count_query.where(
                (ProductModel.name.ilike(term)) | (ProductModel.sku.ilike(term))
            )

        if category_id is not None:
            query = query.where(ProductModel.category_id == category_id)
            count_query = count_query.where(ProductModel.category_id == category_id)

        if status is not None:
            query = query.where(ProductModel.status == status)
            count_query = count_query.where(ProductModel.status == status)

        total = await self.session.scalar(count_query) or 0

        # Sorting
        sort_column = getattr(ProductModel, sort_by, ProductModel.name)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.session.scalars(query)
        items = list(result.all())

        return await build_product_page(self.session, items, total, page, limit)

    async def get_product_by_id(self, product_id: UUID) -> ProductResponse:
        """Fetch a single product by ID.

        Args:
            product_id: UUID of the product.

        Returns:
            Full product response.

        Raises:
            ProductNotFoundException: When the product does not exist.
        """
        product = await self.session.scalar(
            select(ProductModel)
            .where(ProductModel.id == product_id)
            .options(selectinload(ProductModel.category))
        )
        if not product:
            raise ProductNotFoundException

        return ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            unit=product.unit,
            price=product.price,
            costPrice=product.cost_price,
            stock=product.stock,
            reorderLevel=product.reorder_level,
            status=product.status,
            categoryId=product.category_id,
            categoryName=product.category.name if product.category else None,
            createdBy=product.created_by,
            createdAt=product.created_at,
            updatedAt=product.updated_at,
        )

    async def create_product(
        self,
        sku: str,
        name: str,
        unit,
        price: float,
        category_id: UUID,
        description: str | None,
        cost_price: float | None,
        stock: int,
        reorder_level: int,
        status: ProductStatusType,
        created_by: UUID | None = None,
    ) -> CreateProductResponse:
        """Create a new product.

        Args:
            sku: Unique stock-keeping unit.
            name: Product display name.
            unit: Measurement unit.
            price: Selling price.
            category_id: FK to the product's category.
            description: Optional description.
            cost_price: Optional cost price.
            stock: Initial stock quantity.
            reorder_level: Reorder alert threshold.
            status: Product lifecycle status.
            created_by: UUID of the creator.

        Returns:
            Lightweight create response.

        Raises:
            SkuExistsException: When the SKU is already taken.
            CategoryNotActiveException: When the category is inactive.
        """
        validate_input_fields(sku=sku, name=name)

        if not sku_re.match(sku):
            from core.exceptions import UnprocessableEntityError
            raise UnprocessableEntityError(message="Invalid SKU format")

        existing = await self.session.scalar(
            select(ProductModel).where(ProductModel.sku == sku)
        )
        if existing:
            raise SkuExistsException

        category = await self.session.scalar(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        if not category:
            from apps.category.exceptions import CategoryNotFoundException
            raise CategoryNotFoundException
        if not category.is_active:
            raise CategoryNotActiveException

        product = ProductModel.create(
            sku=sku,
            name=name,
            description=description,
            unit=unit,
            price=price,
            cost_price=cost_price,
            stock=stock,
            reorder_level=reorder_level,
            status=status,
            category_id=category_id,
            created_by=created_by,
        )
        self.session.add(product)

        return CreateProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            createdAt=product.created_at,
        )

    async def update_product(
        self,
        product_id: UUID,
        name: str,
        unit,
        price: float,
        category_id: UUID,
        description: str | None,
        cost_price: float | None,
        reorder_level: int,
        status: ProductStatusType,
    ) -> ProductResponse:
        """Update an existing product (full replace).

        Args:
            product_id: UUID of the product to update.
            name: New display name.
            unit: New measurement unit.
            price: New selling price.
            category_id: New category FK.
            description: New description.
            cost_price: New cost price.
            reorder_level: New reorder threshold.
            status: New lifecycle status.

        Returns:
            Updated product response.

        Raises:
            ProductNotFoundException: When the product does not exist.
        """
        product = await self.session.scalar(
            select(ProductModel)
            .where(ProductModel.id == product_id)
            .options(selectinload(ProductModel.category))
        )
        if not product:
            raise ProductNotFoundException

        category = await self.session.scalar(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        if not category:
            from apps.category.exceptions import CategoryNotFoundException
            raise CategoryNotFoundException
        if not category.is_active:
            raise CategoryNotActiveException

        product.name = name
        product.description = description
        product.unit = unit
        product.price = price
        product.cost_price = cost_price
        product.reorder_level = reorder_level
        product.status = status
        product.category_id = category_id

        return ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            unit=product.unit,
            price=product.price,
            costPrice=product.cost_price,
            stock=product.stock,
            reorderLevel=product.reorder_level,
            status=product.status,
            categoryId=product.category_id,
            categoryName=category.name,
            createdBy=product.created_by,
            createdAt=product.created_at,
            updatedAt=product.updated_at,
        )

    async def archive_and_delete(self, product_id: UUID) -> None:
        """Archive a product and then permanently delete it.

        Args:
            product_id: UUID of the product to remove.

        Raises:
            ProductNotFoundException: When the product does not exist.
        """
        product = await self.session.scalar(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        if not product:
            raise ProductNotFoundException

        product.status = ProductStatusType.ARCHIVED

        await self.session.delete(product)
        await self.session.commit()
