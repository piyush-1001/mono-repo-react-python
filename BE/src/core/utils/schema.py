"""Pydantic base schemas and the standard response envelope."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

import constants

T = TypeVar("T")


class CamelCaseModel(BaseModel):
    """Base model that maps snake_case fields to a camelCase API surface."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class SuccessResponse(CamelCaseModel):
    """Payload for success responses that carry no data."""

    message: str = constants.SUCCESS


class ErrorDetail(CamelCaseModel):
    """Single field level validation failure."""

    field: str
    message: str
    type: str | None = None


class BaseValidationResponse(CamelCaseModel):
    """Body returned for 422 request validation failures."""

    status: str = constants.ERROR
    code: int = 422
    message: str = constants.VALIDATION_FAILED
    errors: list[ErrorDetail] = Field(default_factory=list)


class PageMeta(CamelCaseModel):
    """Pagination block attached to list responses."""

    total: int
    page: int
    limit: int
    pages: int


class BaseResponse(BaseModel, Generic[T]):
    """Standard success envelope returned by every endpoint."""

    status: str = constants.SUCCESS
    code: int = 200
    data: T
