"""Category feature exceptions."""

import constants
from core.exceptions import AlreadyExistsError, BadRequestError, NotFoundError


class CategoryNotFoundException(NotFoundError):
    """Raised when a category is not found."""

    message = constants.CATEGORY_NOT_FOUND


class CategoryCodeExistsException(AlreadyExistsError):
    """Raised when a category code already exists."""

    message = constants.CATEGORY_CODE_ALREADY_EXISTS


class CategoryNotEmptyException(BadRequestError):
    """Raised when trying to delete a category that still has products."""

    message = constants.CATEGORY_NOT_EMPTY
