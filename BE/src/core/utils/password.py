"""Password generation utilities."""

import secrets
import string

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = "!@#$%&*"
AMBIGUOUS = "O0Il1"


def create_password(length: int = 12) -> str:
    """Generate a random password containing every required character class.

    :param length: Desired length, at least 8 characters.
    :return: Random password safe to email to a new user.
    """
    if length < 8:
        msg = "Generated passwords must be at least 8 characters"
        raise ValueError(msg)

    alphabet = "".join(
        char for char in LOWERCASE + UPPERCASE + DIGITS + SYMBOLS if char not in AMBIGUOUS
    )
    required = [
        secrets.choice(LOWERCASE),
        secrets.choice(UPPERCASE),
        secrets.choice(DIGITS),
        secrets.choice(SYMBOLS),
    ]
    body = [secrets.choice(alphabet) for _ in range(length - len(required))]
    password = required + body
    secrets.SystemRandom().shuffle(password)
    return "".join(password)
