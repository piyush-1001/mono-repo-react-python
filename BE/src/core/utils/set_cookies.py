"""Auth cookie helpers and Redis token session caching."""

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Response

from config import settings
from constants import TOKEN_SESSION_PREFIX, USER_SESSION_PREFIX
from core.db import redis
from core.utils.hashing import Hash

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def _user_session_key(user_id: UUID) -> str:
    """Redis key holding the active session payload for a user.

    :param user_id: Owner of the session.
    :return: Namespaced Redis key.
    """
    return f"{USER_SESSION_PREFIX}:{user_id}"


def _token_session_key(token: str) -> str:
    """Redis key derived from a token so it can be revoked without storing it.

    :param token: Signed JWT.
    :return: Namespaced, hashed Redis key.
    """
    return f"{TOKEN_SESSION_PREFIX}:{Hash.make(token)}"


async def create_user_token_caching(
    user_id: UUID,
    access_token: str,
    refresh_token: str,
    role: str,
) -> None:
    """Persist a newly issued token pair in Redis.

    Both the user keyed session entry and the token keyed entries are written
    so that sign-out and admin revocation can be O(1) lookups.

    Args:
        user_id: Owner of the session.
        access_token: Signed access token.
        refresh_token: Signed refresh token.
        role: Role stored alongside the session for authorization checks.
    """
    expires_in = settings.ACCESS_TOKEN_LIFETIME
    session = {
        "user_id": str(user_id),
        "role": role,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    pipeline = redis.pipeline()
    pipeline.setex(_user_session_key(user_id), expires_in, json.dumps(session))
    pipeline.setex(_token_session_key(access_token), expires_in, str(user_id))
    pipeline.setex(
        _token_session_key(refresh_token),
        settings.REFRESH_TOKEN_LIFETIME,
        str(user_id),
    )
    await pipeline.execute()


async def revoke_user_session(user_id: UUID) -> None:
    """Drop the user keyed session entry, forcing the next request to refresh.

    :param user_id: Owner of the session.
    """
    await redis.delete(_user_session_key(user_id))


async def revoke_token(token: str) -> None:
    """Revoke a single token by deleting its Redis entry.

    :param token: Signed JWT to invalidate.
    """
    await redis.delete(_token_session_key(token))


async def is_token_revoked(token: str) -> bool:
    """Report whether a token was revoked or has already expired.

    :param token: Signed JWT to check.
    :return: ``True`` when Redis no longer knows about this token.
    """
    return await redis.get(_token_session_key(token)) is None


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> Response:
    """Attach httpOnly auth cookies to a response.

    :param response: Response being returned by an auth endpoint.
    :param access_token: Signed access token.
    :param refresh_token: Signed refresh token.
    :return: The same response, with cookies set.
    """
    max_age = timedelta(seconds=settings.ACCESS_TOKEN_LIFETIME)
    refresh_age = timedelta(seconds=settings.REFRESH_TOKEN_LIFETIME)
    common = {
        "domain": settings.COOKIE_DOMAIN,
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }
    response.set_cookie(ACCESS_COOKIE, access_token, max_age=max_age, **common)
    response.set_cookie(REFRESH_COOKIE, refresh_token, max_age=refresh_age, **common)
    return response


def delete_cookies(response: Response) -> Response:
    """Remove auth cookies from a response.

    :param response: Response being returned by a sign-out endpoint.
    :return: The same response, with cookies cleared.
    """
    for cookie in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            cookie,
            domain=settings.COOKIE_DOMAIN,
            path="/",
        )
    return response
