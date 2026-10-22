"""
FastAPI Lifespan management for startup and shutdown procedures.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI

from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger, setup_logging
from recursive_osint.core.security import hash_password
from recursive_osint.db.base import Base
from recursive_osint.db.models.user import User
from recursive_osint.db.session import engine, AsyncSessionLocal

logger = get_logger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes logging, directories, database schema, and seeds default records."""
    setup_logging()
    logger.info("Initializing %s in [%s] mode...", settings.APP_NAME, settings.ENVIRONMENT)

    # Ensure storage upload directory exists
    upload_dir = Path(settings.STORAGE_LOCAL_ROOT)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Initialize tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized.")

    # Seed demo / default user
    async with AsyncSessionLocal() as session:
        from recursive_osint.db.repositories.user_repo import UserRepository
        repo = UserRepository(session)
        existing = await repo.get_by_email("demo@example.org")
        if not existing:
            demo_user = User(
                email="demo@example.org",
                hashed_password=hash_password("password123"),
                full_name="Lead OSINT Investigator",
                role="investigator",
                is_active=True,
            )
            session.add(demo_user)
            await session.commit()
            logger.info("Created default investigator: demo@example.org (password: password123)")

    yield

    logger.info("Shutting down %s...", settings.APP_NAME)
    await engine.dispose()
