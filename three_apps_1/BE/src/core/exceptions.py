"""Custom application exceptions."""


class CustomException(Exception):
    """Base class for every application exception."""

    status_code: int = 500
    message: str = "Something went wrong"

    def __init__(self, message: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Optional dynamic message overriding the class message.
        """
        self.message = message or self.message
        super().__init__(self.message)


class BadRequestError(CustomException):
    """Raised when the request is malformed."""

    status_code = 400
    message = "Bad request"


class UnauthorizedError(CustomException):
    """Raised when the caller is not authenticated."""

    status_code = 401
    message = "Unauthorized"


class NotFoundError(CustomException):
    """Raised when a resource does not exist."""

    status_code = 404
    message = "Not found"


class AlreadyExistsError(CustomException):
    """Raised when a resource already exists."""

    status_code = 409
    message = "Already exists"
