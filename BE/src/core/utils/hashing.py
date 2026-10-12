"""Hashing and password helpers."""

import base64
import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from config import settings


class Hash:
    """HMAC helpers used to derive Redis keys from opaque values."""

    algorithm = "sha256"

    @classmethod
    def make(cls, value: str) -> str:
        """Return the HMAC-SHA256 digest of ``value`` keyed by the JWT secret.

        :param value: Raw value, typically a JWT or a user id.
        :return: Hex encoded digest safe to use as a cache key.
        """
        key = (settings.JWT_SECRET_KEY or "local-development-key").encode()
        return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()

    @classmethod
    def fingerprint(cls, value: str) -> str:
        """Return a short, url-safe fingerprint used in log lines.

        :param value: Raw value that must not be logged verbatim.
        :return: Base64url digest truncated to 12 characters.
        """
        digest = hashlib.sha256(value.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")[:12]


_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plain text password.

    :param password: Plain text password.
    :return: Argon2id encoded hash.
    """
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Check a plain text password against its stored hash.

    :param password: Plain text candidate password.
    :param hashed: Argon2id hash stored on the user record.
    :return: ``True`` when the password matches, ``False`` otherwise.
    """
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Report whether a stored hash was produced by outdated parameters.

    :param hashed: Argon2id hash stored on the user record.
    :return: ``True`` when the hash should be upgraded on next sign-in.
    """
    try:
        return _hasher.check_needs_rehash(hashed)
    except InvalidHashError:
        return True
