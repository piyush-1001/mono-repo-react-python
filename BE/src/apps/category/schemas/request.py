"""Category request schemas."""

from uuid import UUID

from core.utils.schema import CamelCaseModel


class CreateCategoryRequest(CamelCaseModel):
    """Create category request schema."""

    name: str
    code: str
    description: str | None = None
    isActive: bool = True


class UpdateCategoryRequest(CamelCaseModel):
    """Update category request schema."""

    name: str | None = None
    description: str | None = None
    isActive: bool | None = None


class ListCategoriesRequest(CamelCaseModel):
    """List categories request schema."""

    search: str | None = None
    isActive: bool | None = None
    page: int = 1
    limit: int = 20


class GetCategoryRequest(CamelCaseModel):
    """Get category by ID request schema."""

    categoryId: UUID
