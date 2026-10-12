"""Cross feature helpers: payload decryption, tokens and input validation."""

import base64
import hashlib
import json
import os
import time
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_private_key

import constants
from config import settings
from core.auth import access, refresh
from core.exceptions import BadRequestError, UnauthorizedError, UnprocessableEntityError
from core.utils.hashing import hash_password, verify_password  # re-exported for services
from core.utils.logger import get_logger
from core.utils.password import create_password

import sentry_sdk

logger = get_logger(__name__)

__all__ = [
    "capture_exception",
    "create_password",
    "create_tokens",
    "decrypt",
    "hash_password",
    "validate_email",
    "validate_input_fields",
    "verify_password",
]


def decrypt(
    rsa_key: bytes,
    enc_data: str,
    encrypt_key: str,
    iv_input: str,
    time_check: bool = False,
    timeout: int = constants.PAYLOAD_TIMEOUT,
) -> dict[str, Any]:
    """Decrypt an AES payload whose AES key was wrapped with RSA.

    Args:
        rsa_key: PEM encoded RSA private key loaded on startup.
        enc_data: Base64 encoded AES-CBC ciphertext.
        encrypt_key: Base64 encoded RSA wrapped AES key.
        iv_input: Base64 encoded initial vector.
        time_check: Validate the payload timestamp when ``True``.
        timeout: Accepted payload age in seconds.

    Returns:
        Decoded JSON payload.

    Raises:
        BadRequestError: When the payload cannot be decrypted or parsed.
        UnauthorizedError: When the payload timestamp is outside the window.
    """
    try:
        private_key = load_pem_private_key(rsa_key, password=None)
        aes_key = private_key.decrypt(
            base64.b64decode(encrypt_key),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashlib.sha256()),
                algorithm=hashlib.sha256(),
                label=None,
            ),
        )
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(base64.b64decode(iv_input)))
        decryptor = cipher.decryptor()
        padded = decryptor.update(base64.b64decode(enc_data)) + decryptor.finalize()
        payload = json.loads(_unpad(padded).decode())
    except Exception as exc:
        logger.info("payload decryption failed: %s", exc)
        raise BadRequestError(message=constants.PAYLOAD_INVALID) from exc

    if time_check and not _within_window(payload, timeout):
        raise UnauthorizedError(message=constants.PAYLOAD_EXPIRED)

    return payload


def _unpad(data: bytes) -> bytes:
    """Strip PKCS#7 padding from a decrypted block.

    :param data: Raw ciphertext block with padding appended.
    :return: The block without padding.
    """
    return data[: -data[-1]] if data else data


def _within_window(payload: dict[str, Any], timeout: int) -> bool:
    """Check the request timestamp embedded by the client.

    :param payload: Decoded request payload.
    :param timeout: Accepted age in seconds.
    :return: ``True`` when the payload is fresh enough.
    """
    issued_at = payload.get("_ts")
    if issued_at is None:
        return True
    return abs(time.time() - float(issued_at)) <= timeout


def create_tokens(user_id: UUID, role: str) -> dict[str, str]:
    """Issue an access and refresh token pair.

    :param user_id: Subject of the tokens.
    :param role: Role stored in the token claims.
    :return: Mapping with ``access_token`` and ``refresh_token``.
    """
    return {
        "access_token": access.encode(user_id, role),
        "refresh_token": refresh.encode(user_id, role),
    }


def validate_input_fields(**kwargs: Any) -> None:
    """Reject string fields that arrived empty or whitespace only.

    :param kwargs: Incoming scalar fields keyed by field name.
    :raises UnprocessableEntityError: When a required string field is blank.
    """
    for name, value in kwargs.items():
        if isinstance(value, str) and not value.strip():
            raise UnprocessableEntityError(message=f"{name} must not be empty")


def validate_email(email: str) -> None:
    """Validate the shape of an email address.

    :param email: Address to check.
    :raises UnprocessableEntityError: When the address is malformed.
    """
    if not constants.email_re.match(email or ""):
        raise UnprocessableEntityError(message=constants.EMAIL_FIELD_REQUIRED)


def capture_exception(exc: Exception) -> None:
    """Report an unexpected exception to Sentry without re-raising.

    :param exc: Exception captured by a best effort code path.
    """
    logger.exception("captured exception for Sentry")
    sentry_sdk.capture_exception(exc)


def load_rsa_key() -> bytes:
    """Return the PEM private key used to decrypt request payloads.

    Returns:
        PEM bytes from the setting, or from the mounted secret file.

    Raises:
        BadRequestError: When neither source provides a key.
    """
    if settings.RSA_PRIVATE_KEY:
        return settings.RSA_PRIVATE_KEY.replace("\\n", "\n").encode()

    path = os.getenv("RSA_PRIVATE_KEY_PATH", "")
    if path and os.path.exists(path):
        with open(path, "rb") as key_file:
            return key_file.read()

    raise BadRequestError(message=constants.RSA_KEY_UNAVAILABLE)
