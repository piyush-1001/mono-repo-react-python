"""Product request schemas."""

from uuid import UUID

from core.types import MeasurementUnitType, ProductStatusType, StockMovementType
from core.utils.schema import CamelCaseModel


class CreateProductRequest(CamelCaseModel):
    """Create product request schema."""

    sku: str
    name: str
    description: str | None = None
    unit: MeasurementUnitType
    price: float
    costPrice: float | None = None
    stock: int = 0
    reorderLevel: int = 0
    status: ProductStatusType = ProductStatusType.ACTIVE
    categoryId: UUID


class UpdateProductRequest(CamelCaseModel):
    """Update product request schema (full replace)."""

    name: str
    description: str | None = None
    unit: MeasurementUnitType
    price: float
    costPrice: float | None = None
    reorderLevel: int
    status: ProductStatusType
    categoryId: UUID


class ListProductsRequest(CamelCaseModel):
    """List products request schema with filters, sorting, and pagination."""

    search: str | None = None
    categoryId: UUID | None = None
    status: ProductStatusType | None = None
    page: int = 1
    limit: int = 20
    sortBy: str = "name"
    sortOrder: str = "asc"


class GetProductRequest(CamelCaseModel):
    """Get product by ID request schema."""

    productId: UUID


class StockAdjustmentRequest(CamelCaseModel):
    """Stock adjustment request schema."""

    quantity: int
    movementType: StockMovementType
    reason: str | None = None


class GetProductMovementsRequest(CamelCaseModel):
    """Get product stock movements request schema."""

    productId: UUID
    page: int = 1
    limit: int = 20
