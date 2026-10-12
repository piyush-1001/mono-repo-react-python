"""Category response schemas."""

from datetime import datetime
from uuid import UUID

from core.utils.schema import CamelCaseModel, PageMeta


class CategoryResponse(CamelCaseModel):
    """Full category response schema."""

    id: UUID
    name: str
    code: str
    description: str | None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class CategoryListItemResponse(CamelCaseModel):
    """Category list item with product count."""

    id: UUID
    name: str
    code: str
    isActive: bool
    productCount: int = 0


class CategoryPageResponse(CamelCaseModel):
    """Paginated category list response."""

    items: list[CategoryListItemResponse]
    meta: PageMeta
