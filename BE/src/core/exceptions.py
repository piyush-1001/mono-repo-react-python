"""Base exception hierarchy for the service."""

from fastapi import status

import constants


class CustomException(Exception):
    """Base class for every exception raised by business logic."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = constants.SOMETHING_WENT_WRONG

    def __init__(self, message: str | None = None) -> None:
        """Create the exception, optionally overriding the default message.

        Args:
            message: Overrides the class level message when given.
        """
        self.message = message or self.__class__.message
        super().__init__(self.message)


class BadRequestError(CustomException):
    """Raised when the request cannot be processed."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = constants.INVALID_REQUEST


class UnauthorizedError(CustomException):
    """Raised when the caller is not authenticated."""

    status_code = status.HTTP_401_UNAUTHORIZED
    message = constants.UNAUTHORIZED


class ForbiddenError(CustomException):
    """Raised when the caller lacks permission for the action."""

    status_code = status.HTTP_403_FORBIDDEN
    message = constants.FORBIDDEN


class NotFoundError(CustomException):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    message = constants.NOT_FOUND


class AlreadyExistsError(CustomException):
    """Raised when creating a resource that already exists."""

    status_code = status.HTTP_409_CONFLICT
    message = "Resource already exists"


class UnprocessableEntityError(CustomException):
    """Raised when domain validation of the payload fails."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = constants.VALIDATION_FAILED


class TooManyRequestsError(CustomException):
    """Raised when the caller exceeds the configured rate limit."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = constants.TOO_MANY_REQUESTS


class InvalidJWTTokenException(UnauthorizedError):
    """Raised when a JWT is malformed, expired or revoked."""

    message = constants.INVALID_TOKEN


class InvalidRoleException(NotFoundError):
    """Raised when a role name does not map to a known role."""

    message = constants.ROLE_INVALID


class UnexpectedResponse(Exception):
    """Raised when an external HTTP client returns an unusable response."""

    def __init__(self, message: str = "Unexpected response from upstream service") -> None:
        """Create the exception.

        Args:
            message: Human readable description of the upstream failure.
        """
        self.message = message
        super().__init__(message)
