"""Product response schemas."""

from datetime import datetime
from uuid import UUID

from core.types import MeasurementUnitType, ProductStatusType, StockMovementType
from core.utils.schema import CamelCaseModel, PageMeta


class ProductResponse(CamelCaseModel):
    """Full product response schema."""

    id: UUID
    sku: str
    name: str
    description: str | None
    unit: MeasurementUnitType
    price: float
    costPrice: float | None
    stock: int
    reorderLevel: int
    status: ProductStatusType
    categoryId: UUID
    categoryName: str | None = None
    createdBy: UUID | None = None
    createdAt: datetime
    updatedAt: datetime


class ProductListItemResponse(CamelCaseModel):
    """Product list item for paginated responses."""

    id: UUID
    sku: str
    name: str
    unit: MeasurementUnitType
    price: float
    stock: int
    reorderLevel: int
    status: ProductStatusType
    categoryId: UUID
    categoryName: str | None = None
    createdAt: datetime


class ProductPageResponse(CamelCaseModel):
    """Paginated product list response."""

    items: list[ProductListItemResponse]
    meta: PageMeta


class CreateProductResponse(CamelCaseModel):
    """Lightweight create product response."""

    id: UUID
    sku: str
    name: str
    createdAt: datetime


class StockMovementResponse(CamelCaseModel):
    """Single stock movement record."""

    id: UUID
    productId: UUID
    quantity: int
    movementType: StockMovementType
    reason: str | None
    balanceAfter: int
    createdBy: UUID | None = None
    createdAt: datetime


class LowStockItemResponse(CamelCaseModel):
    """Product item in low-stock alert response."""

    id: UUID
    sku: str
    name: str
    stock: int
    reorderLevel: int
    categoryId: UUID


class StockSummaryResponse(CamelCaseModel):
    """Aggregated stock statistics."""

    totalProducts: int
    totalValue: float
    lowStockCount: int
    outOfStockCount: int
