"""Category model."""

import uuid
from typing import Self

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base
from core.utils.mixins import TimeStampMixin, UUIDPrimaryKeyMixin


class CategoryModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """Category for grouping products."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __str__(self) -> str:
        """String representation."""
        return f"Category(id={self.id}, code={self.code})"

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        description: str | None = None,
        is_active: bool = True,
    ) -> Self:
        """Create a new category instance.

        Args:
            name: Category display name.
            code: Unique category code.
            description: Optional human-readable description.
            is_active: Whether the category is active.

        Returns:
            CategoryModel instance.
        """
        return cls(id=uuid.uuid4(), name=name, code=code, description=description, is_active=is_active)
