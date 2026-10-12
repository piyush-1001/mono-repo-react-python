"""Stock movement service."""

import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.product.exceptions import (
    InsufficientStockException,
    NegativeStockException,
    ProductNotFoundException,
)
from apps.product.models.product import ProductModel
from apps.product.models.stock_movement import StockMovementModel
from apps.product.schemas.response import (
    LowStockItemResponse,
    StockMovementResponse,
    StockSummaryResponse,
)
from constants import LOW_STOCK_ALERT_BATCH
from core.db import db_session
from core.types import StockMovementType


class StockMovementService:
    """Service for managing stock movements and inventory statistics."""

    def __init__(self, session: db_session) -> None:
        """Initialize stock movement service.

        Args:
            session: Async database session.
        """
        self.session = session

    async def apply_stock_adjustment(
        self,
        product_id: UUID,
        quantity: int,
        movement_type: StockMovementType,
        reason: str | None,
        performed_by: UUID | None = None,
    ) -> StockMovementResponse:
        """Record a stock movement and update the product balance.

        Args:
            product_id: UUID of the product to adjust.
            quantity: Absolute quantity (sign derived from type).
            movement_type: IN, OUT, or ADJUST.
            reason: Optional explanation.
            performed_by: UUID of the user performing the adjustment.

        Returns:
            The created stock movement record.

        Raises:
            ProductNotFoundException: When the product does not exist.
            NegativeStockException: When the movement would make stock negative.
            InsufficientStockException: When OUT movement exceeds available stock.
        """
        product = await self.session.scalar(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        if not product:
            raise ProductNotFoundException

        # Compute the new balance
        if movement_type == StockMovementType.IN:
            delta = abs(quantity)
        elif movement_type == StockMovementType.OUT:
            delta = -abs(quantity)
        else:  # ADJUST
            delta = quantity  # can be positive or negative

        new_balance = product.stock + delta

        if new_balance < 0:
            raise NegativeStockException

        if movement_type == StockMovementType.OUT and product.stock < abs(quantity):
            raise InsufficientStockException

        product.stock = new_balance

        movement = StockMovementModel.create(
            product_id=product_id,
            quantity=abs(quantity),
            movement_type=movement_type,
            reason=reason,
            balance_after=new_balance,
            created_by=performed_by,
        )
        self.session.add(movement)

        return StockMovementResponse(
            id=movement.id,
            productId=movement.product_id,
            quantity=movement.quantity,
            movementType=movement.movement_type,
            reason=movement.reason,
            balanceAfter=movement.balance_after,
            createdBy=movement.created_by,
            createdAt=movement.created_at,
        )

    async def get_product_movements(
        self, product_id: UUID, page: int, limit: int
    ) -> tuple[list[StockMovementResponse], int]:
        """Fetch paginated stock movements for a product.

        Args:
            product_id: UUID of the product.
            page: Page number (1-indexed).
            limit: Items per page.

        Returns:
            Tuple of (list of movement responses, total count).

        Raises:
            ProductNotFoundException: When the product does not exist.
        """
        product = await self.session.scalar(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        if not product:
            raise ProductNotFoundException

        total = await self.session.scalar(
            select(func.count(StockMovementModel.id)).where(
                StockMovementModel.product_id == product_id
            )
        ) or 0

        offset = (page - 1) * limit
        result = await self.session.scalars(
            select(StockMovementModel)
            .where(StockMovementModel.product_id == product_id)
            .order_by(StockMovementModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        movements = [
            StockMovementResponse(
                id=m.id,
                productId=m.product_id,
                quantity=m.quantity,
                movementType=m.movement_type,
                reason=m.reason,
                balanceAfter=m.balance_after,
                createdBy=m.created_by,
                createdAt=m.created_at,
            )
            for m in result.all()
        ]

        return movements, total

    async def get_low_stock_products(self) -> list[LowStockItemResponse]:
        """Fetch products where stock is at or below the reorder level.

        Returns:
            List of low-stock products, capped at LOW_STOCK_ALERT_BATCH.
        """
        result = await self.session.scalars(
            select(ProductModel)
            .where(ProductModel.stock <= ProductModel.reorder_level)
            .where(ProductModel.status == "ACTIVE")
            .limit(LOW_STOCK_ALERT_BATCH)
        )
        return [
            LowStockItemResponse(
                id=p.id,
                sku=p.sku,
                name=p.name,
                stock=p.stock,
                reorderLevel=p.reorder_level,
                categoryId=p.category_id,
            )
            for p in result.all()
        ]

    async def get_stock_summary(self) -> StockSummaryResponse:
        """Compute aggregate stock statistics across all products.

        Returns:
            Stock summary with totals and counts.
        """
        total_row = await self.session.execute(
            select(
                func.count(ProductModel.id).label("total_products"),
                func.coalesce(func.sum(ProductModel.stock * ProductModel.price), 0).label(
                    "total_value"
                ),
                func.sum(
                    ProductModel.stock <= ProductModel.reorder_level
                ).label("low_stock"),
                func.sum(ProductModel.stock <= 0).label("out_of_stock"),
            ).where(ProductModel.status == "ACTIVE")
        )
        row = total_row.one()

        return StockSummaryResponse(
            totalProducts=row.total_products or 0,
            totalValue=float(row.total_value or 0),
            lowStockCount=int(row.low_stock or 0),
            outOfStockCount=int(row.out_of_stock or 0),
        )
