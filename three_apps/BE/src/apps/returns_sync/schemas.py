"""Returns sync schemas."""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

MAX_REFUND_DAYS = 14


def to_camel(value: str) -> str:
    """Convert a snake_case field name to camelCase.

    Args:
        value: Field name in snake_case.

    Returns:
        Field name in camelCase.
    """
    head, *rest = value.split("_")
    return head + "".join(word.capitalize() for word in rest)


class CamelCaseModel(BaseModel):
    """Base schema that exposes snake_case fields as camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class BaseResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    status: str = "SUCCESS"
    code: int = 200
    data: T | None = None


class CreateReturnsSyncRequest(CamelCaseModel):
    """Create a returns sync request schema."""

    barcode: str
    device_id: str
    payload: dict = {}
    reason: str | None = None
    user_id: UUID | None = None


class ReturnsSyncResponse(CamelCaseModel):
    """Returns sync response schema."""

    id: UUID
    barcode: str
    device_id: str
    status: str
    payload: dict
    created_by_email: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateReturnsSyncResponse(CamelCaseModel):
    """Create returns sync response schema."""

    id: UUID
    barcode: str
    created_at: datetime
