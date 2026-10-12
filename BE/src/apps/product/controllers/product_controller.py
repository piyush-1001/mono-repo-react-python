"""Product controller."""

import math
from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path, Query, status
from fastapi.responses import JSONResponse

from apps.product.schemas.request import (
    CreateProductRequest,
    ListProductsRequest,
    StockAdjustmentRequest,
    UpdateProductRequest,
)
from apps.product.schemas.response import (
    CreateProductResponse,
    LowStockItemResponse,
    ProductListItemResponse,
    ProductPageResponse,
    ProductResponse,
    StockMovementResponse,
)
from apps.product.services.product import ProductService
from apps.product.services.stock_movement import StockMovementService
from core.auth import AdminHasPermission, HasPermission
from core.db import db_session
from core.types import RoleType
from core.utils.schema import BaseResponse, PageMeta

router = APIRouter(prefix="/api/product", tags=["Product"])

from fastapi import APIRouter


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    operation_id="list_products",
    description="List products with filters, sorting, and pagination",
    name="list_products",
)
async def list_products(
    service: Annotated[ProductService, Depends()],
    request: ListProductsRequest = Depends(),
) -> BaseResponse[ProductPageResponse]:
    """List products with filters, sorting, and pagination."""
    data = await service.list_products(
        search=request.search,
        category_id=request.categoryId,
        status=request.status,
        page=request.page,
        limit=request.limit,
        sort_by=request.sortBy,
        sort_order=request.sortOrder,
    )
    return BaseResponse(data=data)


@router.get(
    "/low-stock",
    status_code=status.HTTP_200_OK,
    operation_id="get_low_stock_products",
    description="List products where stock is at or below reorder level",
    name="get_low_stock_products",
)
async def get_low_stock_products(
    service: Annotated[StockMovementService, Depends()],
) -> BaseResponse[list[LowStockItemResponse]]:
    """List products where stock is at or below the reorder level."""
    data = await service.get_low_stock_products()
    return BaseResponse(data=data)


@router.get(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    operation_id="get_product",
    description="Fetch a single product by ID",
    name="get_product",
)
async def get_product(
    product_id: Annotated[UUID, Path(description="Product ID")],
    service: Annotated[ProductService, Depends()],
) -> BaseResponse[ProductResponse]:
    """Fetch a single product by ID."""
    data = await service.get_product_by_id(product_id)
    return BaseResponse(data=data)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_product",
    description="Create a new product",
    name="create_product",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
)
async def create_product(
    service: Annotated[ProductService, Depends()],
    body: CreateProductRequest = Body(...),
) -> BaseResponse[CreateProductResponse]:
    """Create a new product."""
    data = await service.create_product(**body.model_dump())
    return BaseResponse(data=data)


@router.put(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    operation_id="update_product",
    description="Update an existing product (full replace)",
    name="update_product",
)
async def update_product(
    product_id: Annotated[UUID, Path(description="Product ID")],
    service: Annotated[ProductService, Depends()],
    body: UpdateProductRequest = Body(...),
) -> BaseResponse[ProductResponse]:
    """Update an existing product (full replace)."""
    data = await service.update_product(product_id, **body.model_dump())
    return BaseResponse(data=data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    operation_id="delete_product",
    description="Archive and permanently delete a product",
    name="delete_product",
    dependencies=[Depends(AdminHasPermission())],
)
async def delete_product(
    product_id: Annotated[UUID, Path(description="Product ID")],
    service: Annotated[ProductService, Depends()],
) -> BaseResponse[None]:
    """Archive and permanently delete a product."""
    await service.archive_and_delete(product_id)
    return BaseResponse(data=None)


@router.post(
    "/{product_id}/stock-adjustment",
    status_code=status.HTTP_200_OK,
    operation_id="adjust_stock",
    description="Record a stock movement for a product",
    name="adjust_stock",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
)
async def adjust_stock(
    product_id: Annotated[UUID, Path(description="Product ID")],
    service: Annotated[StockMovementService, Depends()],
    body: StockAdjustmentRequest = Body(...),
) -> BaseResponse[StockMovementResponse]:
    """Record a stock movement (IN, OUT, or ADJUST) for a product."""
    data = await service.apply_stock_adjustment(
        product_id=product_id,
        quantity=body.quantity,
        movement_type=body.movementType,
        reason=body.reason,
    )
    return BaseResponse(data=data)


@router.get(
    "/{product_id}/movements",
    status_code=status.HTTP_200_OK,
    operation_id="get_product_movements",
    description="Fetch paginated stock movements for a product",
    name="get_product_movements",
)
async def get_product_movements(
    product_id: Annotated[UUID, Path(description="Product ID")],
    service: Annotated[StockMovementService, Depends()],
    page: Annotated[int, Query(description="Page number")] = 1,
    limit: Annotated[int, Query(description="Items per page")] = 20,
) -> JSONResponse:
    """Fetch paginated stock movements for a product."""
    movements, total = await service.get_product_movements(
        product_id=product_id, page=page, limit=limit
    )
    pages = math.ceil(total / limit) if limit > 0 else 0
    meta = PageMeta(total=total, page=page, limit=limit, pages=pages)

    return JSONResponse(
        content={
            "status": "SUCCESS",
            "code": 200,
            "data": {
                "items": [m.model_dump(by_alias=True) for m in movements],
                "meta": meta.model_dump(by_alias=True),
            },
        }
    )
