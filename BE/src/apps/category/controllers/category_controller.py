"""Category controller."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.category.exceptions import CategoryNotFoundException
from apps.category.schemas.request import (
    CreateCategoryRequest,
    ListCategoriesRequest,
    UpdateCategoryRequest,
)
from apps.category.schemas.response import (
    CategoryPageResponse,
    CategoryResponse,
)
from apps.category.services.category import CategoryService
from core.auth import AdminHasPermission, HasPermission
from core.db import db_session
from core.types import RoleType
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/api/category", tags=["Category"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    operation_id="list_categories",
    description="List categories with pagination and optional filters",
    name="list_categories",
)
async def list_categories(
    service: Annotated[CategoryService, Depends()],
    request: ListCategoriesRequest = Depends(),
) -> BaseResponse[CategoryPageResponse]:
    """List categories with pagination and optional filters."""
    data = await service.list_categories(
        search=request.search,
        is_active=request.isActive,
        page=request.page,
        limit=request.limit,
    )
    return BaseResponse(data=data)


@router.get(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    operation_id="get_category",
    description="Fetch a single category by ID",
    name="get_category",
)
async def get_category(
    category_id: Annotated[UUID, Path(description="Category ID")],
    service: Annotated[CategoryService, Depends()],
) -> BaseResponse[CategoryResponse]:
    """Fetch a single category by ID."""
    data = await service.get_category_by_id(category_id)
    return BaseResponse(data=data)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_category",
    description="Create a new product category",
    name="create_category",
    dependencies=[Depends(HasPermission(RoleType.ADMIN, RoleType.STAFF))],
)
async def create_category(
    service: Annotated[CategoryService, Depends()],
    body: CreateCategoryRequest = Body(...),
) -> BaseResponse[CategoryResponse]:
    """Create a new product category."""
    data = await service.create_category(**body.model_dump())
    return BaseResponse(data=data)


@router.put(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    operation_id="update_category",
    description="Update an existing category",
    name="update_category",
)
async def update_category(
    category_id: Annotated[UUID, Path(description="Category ID")],
    service: Annotated[CategoryService, Depends()],
    body: UpdateCategoryRequest = Body(...),
) -> BaseResponse[CategoryResponse]:
    """Update an existing category."""
    data = await service.update_category(category_id, **body.model_dump())
    return BaseResponse(data=data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    operation_id="delete_category",
    description="Delete a category (only if it has no products)",
    name="delete_category",
    dependencies=[Depends(AdminHasPermission())],
)
async def delete_category(
    category_id: Annotated[UUID, Path(description="Category ID")],
    service: Annotated[CategoryService, Depends()],
) -> BaseResponse[None]:
    """Delete a category (only if it has no products)."""
    await service.delete_category(category_id)
    return BaseResponse(data=None)
