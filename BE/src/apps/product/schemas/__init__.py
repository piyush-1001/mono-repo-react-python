"""Product schemas."""

# --- Requests ---
from apps.product.schemas.request import (
    CreateProductRequest,
    GetProductRequest,
    ListProductsRequest,
    StockAdjustmentRequest,
    UpdateProductRequest,
)

# --- Responses ---
from apps.product.schemas.response import (
    CreateProductResponse,
    LowStockItemResponse,
    ProductListItemResponse,
    ProductPageResponse,
    ProductResponse,
    StockMovementResponse,
    StockSummaryResponse,
)

__all__ = [
    # Requests
    "CreateProductRequest",
    "GetProductRequest",
    "ListProductsRequest",
    "StockAdjustmentRequest",
    "UpdateProductRequest",
    # Responses
    "CreateProductResponse",
    "LowStockItemResponse",
    "ProductListItemResponse",
    "ProductPageResponse",
    "ProductResponse",
    "StockMovementResponse",
    "StockSummaryResponse",
]
