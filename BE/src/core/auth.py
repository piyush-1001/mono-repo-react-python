"""JWT encoding/decoding and role based authorization dependencies."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, Request
from jwt.exceptions import PyJWTError

from config import settings
from constants import MISSING_TOKEN
from core.exceptions import ForbiddenError, InvalidJWTTokenException, UnauthorizedError
from core.types import RoleType, TokenType
from core.utils.hashing import Hash
from core.utils.logger import get_logger

logger = get_logger(__name__)


class JWToken:
    """Signs and verifies JWTs for one token flavour."""

    def __init__(
        self,
        token_type: TokenType,
        lifetime: int,
        secret: str | None = None,
        algorithm: str | None = None,
    ) -> None:
        """Create a token instance.

        Args:
            token_type: Flavour written into the ``token_type`` claim.
            lifetime: Lifetime in seconds.
            secret: Signing secret, defaults to ``settings.JWT_SECRET_KEY``.
            algorithm: Signing algorithm, defaults to ``settings.JWT_ALGORITHM``.
        """
        self.token_type = token_type
        self.lifetime = lifetime
        self.secret = secret or settings.JWT_SECRET_KEY or "local-development-secret-key"
        self.algorithm = algorithm or settings.JWT_ALGORITHM

    def encode(self, user_id: UUID, role: str) -> str:
        """Sign a token for a user.

        :param user_id: Subject of the token.
        :param role: Role stored in the ``role`` claim.
        :return: Encoded JWT string.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "role": role,
            "token_type": self.token_type.value,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self.lifetime)).timestamp()),
            "jti": Hash.fingerprint(f"{user_id}:{now.isoformat()}"),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        """Verify a token and return its claims.

        :param token: Encoded JWT.
        :return: Decoded claims.
        :raises InvalidJWTTokenException: When the token is expired or malformed.
        """
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except PyJWTError as exc:
            logger.info("token rejected: %s", exc)
            raise InvalidJWTTokenException from exc

    def revoke_key(self, token: str) -> str:
        """Return the Redis key under which this token is cached.

        :param token: Encoded JWT.
        :return: Hashed, namespaced Redis key.
        """
        return f"session:token:{Hash.make(token)}"


access = JWToken(TokenType.ACCESS, settings.ACCESS_TOKEN_LIFETIME)
refresh = JWToken(TokenType.REFRESH, settings.REFRESH_TOKEN_LIFETIME)
admin_access = JWToken(TokenType.ADMIN_ACCESS, settings.ACCESS_TOKEN_LIFETIME)
admin_refresh = JWToken(TokenType.ADMIN_REFRESH, settings.REFRESH_TOKEN_LIFETIME)


async def get_token_from_request(request: Request, token_type: TokenType) -> str:
    """Pull a token out of the Authorization header or the auth cookies.

    :param request: Incoming request.
    :param token_type: Which cookie to fall back to.
    :return: Raw token string.
    :raises UnauthorizedError: When no token is present anywhere.
    """
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1]

    cookie = "refresh_token" if token_type is TokenType.REFRESH else "access_token"
    token = request.cookies.get(cookie)
    if not token:
        raise UnauthorizedError(message=MISSING_TOKEN)
    return token


class BaseHasPermission:
    """Resolves the caller from the request and checks the role allowance."""

    def __init__(self, allowed_roles: list[RoleType]) -> None:
        """Store the roles permitted on the endpoint.

        Args:
            allowed_roles: Roles allowed through, ``RoleType.ANY`` allows all.
        """
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request) -> dict[str, Any]:
        """Authenticate the caller and return the token claims.

        :param request: Incoming request.
        :return: Verified token claims.
        :raises ForbiddenError: When the caller role is not allowed.
        """
        from core.db import redis

        token = await get_token_from_request(request, TokenType.ACCESS)
        claims = access.decode(token)
        if claims.get("token_type") != TokenType.ACCESS.value:
            raise InvalidJWTTokenException

        if await redis.get(access.revoke_key(token)) is None:
            raise InvalidJWTTokenException

        role = claims.get("role")
        if RoleType.ANY in self.allowed_roles:
            return claims

        if RoleType.OPTIONAL in self.allowed_roles and role is None:
            return claims

        if role not in {allowed.value for allowed in self.allowed_roles}:
            raise ForbiddenError(message="Insufficient role for this endpoint")

        return claims


class HasPermission(BaseHasPermission):
    """Dependency factory guarding an endpoint by role."""

    def __init__(self, *roles: RoleType) -> None:
        """Collect the allowed roles.

        Args:
            *roles: Roles permitted on the endpoint.
        """
        super().__init__(list(roles))


class AdminHasPermission(BaseHasPermission):
    """Dependency for admin only endpoints."""

    def __init__(self) -> None:
        """Allow only administrators through."""
        super().__init__([RoleType.ADMIN])


UserClaims = Annotated[dict[str, Any], Depends(HasPermission(RoleType.ANY))]
AdminClaims = Annotated[dict[str, Any], Depends(AdminHasPermission())]


def user_id_from(claims: dict[str, Any]) -> UUID:
    """Read the subject out of verified token claims.

    :param claims: Claims returned by :class:`BaseHasPermission`.
    :return: User id as a UUID.
    """
    return UUID(claims["sub"])
