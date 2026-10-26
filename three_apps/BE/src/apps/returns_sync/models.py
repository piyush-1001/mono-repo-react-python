"""Returns sync models."""

import uuid
from datetime import datetime
from typing import Self

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for the returns sync models."""


class UUIDPrimaryKeyMixin:
    """Provides a UUID primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimeStampMixin:
    """Provides created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ReturnsSyncModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """One barcode batch pushed from a handheld device."""

    __tablename__ = "returns_sync"

    barcode: Mapped[str] = mapped_column(String(64))
    device_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    payload: Mapped[str] = mapped_column(String(2000), default="{}")
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    def __str__(self) -> str:
        """String representation."""
        return (
            f"<ReturnsSync>(id={self.id}, barcode={self.barcode}, "
            f"device_id={self.device_id}, status={self.status})"
        )

    @classmethod
    def create(
        cls,
        barcode: str,
        device_id: str,
        payload: str = "{}",
        created_by: uuid.UUID | None = None,
    ) -> Self:
        """Create a new returns sync row.

        Args:
            barcode: Barcode scanned on the handheld.
            device_id: Identifier of the handheld that pushed the batch.
            payload: Raw JSON payload received from the device.
            created_by: Optional user that triggered the sync.

        Returns:
            ReturnsSyncModel instance.
        """
        return cls(
            barcode=barcode,
            device_id=device_id,
            payload=payload,
            created_by=created_by,
        )
