"""User model."""

import uuid
from datetime import datetime
from typing import Optional, Self

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.types import RoleType
from core.utils.mixins import TimeStampMixin, UUIDPrimaryKeyMixin


class UserModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """User account record."""

    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column()
    role: Mapped[RoleType] = mapped_column(default=RoleType.USER)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    creator: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[created_by],
        remote_side="UserModel.id",
        viewonly=True,
    )
    editor: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[updated_by],
        remote_side="UserModel.id",
        viewonly=True,
    )

    def __str__(self) -> str:
        """String representation."""
        return f"UserModel(id={self.id}, email={self.email})"

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
        role: RoleType = RoleType.USER,
        phone: str | None = None,
        is_active: bool = True,
        created_by: int | None = None,
        updated_by: int | None = None,
    ) -> Self:
        """Create a new user instance.

        Args:
            first_name: User's first name.
            last_name: User's last name.
            email: Unique email address.
            password_hash: Argon2id hash of the password.
            role: Platform role, defaults to USER.
            phone: Optional unique phone number.
            is_active: Whether the account is active, defaults to True.
            created_by: ID of the user who created this record.
            updated_by: ID of the user who last updated this record.

        Returns:
            UserModel instance with a freshly generated UUID.
        """
        return cls(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by,
        )
