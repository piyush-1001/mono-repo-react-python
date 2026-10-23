"""Database session helpers."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/returns"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session that commits on success.

    Yields:
        Async database session.
    """
    async with async_session() as session:
        async with session.begin():
            yield session
