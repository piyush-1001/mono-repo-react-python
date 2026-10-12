"""Product model."""

import uuid
from typing import TYPE_CHECKING, Optional, Self

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.product.types import ProductSortField
from core.db import Base
from core.types import MeasurementUnitType, ProductStatusType
from core.utils.mixins import TimeStampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.category.models.category import CategoryModel
    from apps.user.models.user import UserModel
    from apps.product.models.stock_movement import StockMovementModel


class ProductModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """Product inventory item."""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    unit: Mapped[MeasurementUnitType] = mapped_column(default=MeasurementUnitType.PIECE)
    price: Mapped[float] = mapped_column()
    cost_price: Mapped[float | None] = mapped_column(nullable=True)
    stock: Mapped[int] = mapped_column(default=0)
    reorder_level: Mapped[int] = mapped_column(default=0)
    status: Mapped[ProductStatusType] = mapped_column(
        default=ProductStatusType.ACTIVE
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    category: Mapped["CategoryModel"] = relationship(
        "CategoryModel", foreign_keys=[category_id]
    )
    creator: Mapped[Optional["UserModel"]] = relationship(
        "UserModel", foreign_keys=[created_by]
    )

    def __str__(self) -> str:
        """String representation."""
        return f"Product(id={self.id}, sku={self.sku})"

    @classmethod
    def create(
        cls,
        sku: str,
        name: str,
        unit: MeasurementUnitType,
        price: float,
        category_id: uuid.UUID,
        description: str | None = None,
        cost_price: float | None = None,
        stock: int = 0,
        reorder_level: int = 0,
        status: ProductStatusType = ProductStatusType.ACTIVE,
        created_by: uuid.UUID | None = None,
    ) -> Self:
        """Create a new product instance.

        Args:
            sku: Unique stock-keeping unit.
            name: Product display name.
            unit: Measurement unit.
            price: Selling price.
            category_id: FK to the product's category.
            description: Optional description.
            cost_price: Optional cost price.
            stock: Initial stock quantity.
            reorder_level: Stock level that triggers reorder alerts.
            status: Product lifecycle status.
            created_by: UUID of the user who created this product.

        Returns:
            ProductModel instance.
        """
        return cls(
            id=uuid.uuid4(),
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
