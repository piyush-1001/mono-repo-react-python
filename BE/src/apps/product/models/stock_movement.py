"""Stock movement model."""

import uuid
from typing import TYPE_CHECKING, Optional, Self

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.types import StockMovementType
from core.utils.mixins import TimeStampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.product.models.product import ProductModel
    from apps.user.models.user import UserModel


class StockMovementModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """Immutable ledger entry for stock quantity changes."""

    __tablename__ = "stock_movements"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    movement_type: Mapped[StockMovementType] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    balance_after: Mapped[int] = mapped_column(nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    product: Mapped["ProductModel"] = relationship(
        "ProductModel", foreign_keys=[product_id]
    )
    creator: Mapped[Optional["UserModel"]] = relationship(
        "UserModel", foreign_keys=[created_by]
    )

    def __str__(self) -> str:
        """String representation."""
        return f"StockMovement(id={self.id}, product_id={self.product_id}, type={self.movement_type})"

    @classmethod
    def create(
        cls,
        product_id: uuid.UUID,
        quantity: int,
        movement_type: StockMovementType,
        balance_after: int,
        reason: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> Self:
        """Create a new stock movement entry.

        Args:
            product_id: FK to the product being adjusted.
            quantity: Absolute quantity changed (sign determined by type).
            movement_type: IN, OUT, or ADJUST.
            balance_after: Stock level after this movement.
            reason: Optional explanation of the adjustment.
            created_by: UUID of the user who recorded this movement.

        Returns:
            StockMovementModel instance.
        """
        return cls(
            id=uuid.uuid4(),
            product_id=product_id,
            quantity=quantity,
            movement_type=movement_type,
            reason=reason,
            balance_after=balance_after,
            created_by=created_by,
        )
