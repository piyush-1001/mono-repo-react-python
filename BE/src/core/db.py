"""Database engine, session factory, Redis client and rate limit dependency."""

from collections.abc import AsyncGenerator

from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings
from constants import RATE_LIMIT_PREFIX
from core.exceptions import TooManyRequestsError


class Base(DeclarativeBase):
    """Declarative base shared by every model in the project."""


engine = create_async_engine(
    settings.DATABASE_URL or "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory",
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

_pool = ConnectionPool.from_url(settings.redis_url, max_connections=50, decode_responses=True)
redis = Redis(connection_pool=_pool)


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session wrapped in a transaction.

    The transaction commits when the request body finishes without raising and
    rolls back on any exception, so services never call ``commit`` themselves.

    Yields:
        Async SQLAlchemy session bound to a running transaction.
    """
    async with async_session() as session:
        async with session.begin():
            yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session for dependencies that must not manage a transaction.

    Yields:
        Async SQLAlchemy session without an explicit transaction block.
    """
    async with async_session() as session:
        yield session


rate_limit = RateLimiter(
    times=settings.RATE_LIMIT_REQUESTS,
    limit=settings.RATE_LIMIT_REQUESTS,
    time_window=settings.RATE_LIMIT_WINDOW,
    cost=1,
)


async def init_rate_limiter() -> None:
    """Bind :class:`FastAPILimiter` to the Redis client on application startup."""
    await FastAPILimiter.init(
        redis,
        prefix=RATE_LIMIT_PREFIX,
        http_limit_callback=_limit_reached,
    )


async def close_rate_limiter() -> None:
    """Release the limiter resources on application shutdown."""
    await FastAPILimiter.close()


async def _limit_reached(request: Request, _response) -> None:
    """Raise a 429 with the shared message when the window is exhausted.

    :param request: Request that tripped the limiter.
    :param _response: Limiter response object, unused.
    :raises TooManyRequestsError: Always.
    """
    raise TooManyRequestsError


async def ping_database() -> bool:
    """Return ``True`` when the database answers a trivial query."""
    try:
        async with async_session() as session:
            await session.scalar(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - health probe reports availability, not the cause
        return False
    return True
