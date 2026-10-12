"""Product feature exceptions."""

import constants
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class ProductNotFoundException(NotFoundError):
    """Raised when a product is not found."""

    message = constants.PRODUCT_NOT_FOUND


class SkuExistsException(AlreadyExistsError):
    """Raised when a SKU already exists."""

    message = constants.SKU_ALREADY_EXISTS


class NegativeStockException(BadRequestError):
    """Raised when a stock movement would make stock negative."""

    message = constants.STOCK_MOVEMENT_NOT_ALLOWED


class InsufficientStockException(BadRequestError):
    """Raised when there is not enough stock for the requested movement."""

    message = constants.INSUFFICIENT_STOCK


class CategoryNotActiveException(BadRequestError):
    """Raised when trying to assign an inactive category to a product."""

    message = "Category is not active"
