"""User feature exceptions."""

from core.exceptions import AlreadyExistsError, ForbiddenError, NotFoundError, UnauthorizedError

import constants


class UserNotFoundException(NotFoundError):
    """Raised when a user record does not exist."""

    message = constants.USER_NOT_FOUND


class InvalidCredentialsException(UnauthorizedError):
    """Raised when sign-in credentials do not match any user."""

    message = constants.INVALID_CREDENTIALS


class DuplicateEmailException(AlreadyExistsError):
    """Raised when a user with the given email already exists."""

    message = constants.EMAIL_ALREADY_EXISTS


class DuplicatePhoneException(AlreadyExistsError):
    """Raised when a user with the given phone number already exists."""

    message = constants.PHONE_ALREADY_EXISTS


class InactiveUserException(UnauthorizedError):
    """Raised when a deactivated user attempts to sign in."""

    message = constants.ACCOUNT_INACTIVE


class SelfDeactivationException(ForbiddenError):
    """Raised when a user attempts to deactivate their own account."""

    message = constants.SELF_DEACTIVATION_NOT_ALLOWED
