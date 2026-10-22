"""
Database engine and async session factory.
Supports Neon PostgreSQL with serverless pooling and local SQLite.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from recursive_osint.config import settings

# Engine configuration depending on SQLite or PostgreSQL
engine_kwargs = {
    "echo": settings.DEBUG,
}

if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Neon connection settings
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    if settings.DATABASE_USE_NULLPOOL:
        # In serverless lambda environments, avoid holding open connection pools
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
