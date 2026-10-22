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
    """Initializes logging, directories, database schema, and validates configurations."""
    setup_logging()
    logger.info("Initializing %s in [%s] mode...", settings.APP_NAME, settings.ENVIRONMENT)

    # Validate production readiness assertions
    settings.validate_production_readiness()

    # Ensure storage upload directory exists safely without crashing read-only serverless filesystems
    try:
        upload_dir = Path(settings.STORAGE_LOCAL_ROOT)
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Storage directory initialized at: %s", upload_dir.resolve())
    except (OSError, PermissionError) as exc:
        logger.warning(
            "Could not create configured storage directory '%s': %s. "
            "Attempting fallback to temporary directory.",
            settings.STORAGE_LOCAL_ROOT,
            exc,
        )
        try:
            import tempfile
            fallback_dir = Path(tempfile.gettempdir()) / "storage" / "uploads"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            settings.STORAGE_LOCAL_ROOT = str(fallback_dir)
            logger.info("Fell back to temporary storage directory at: %s", fallback_dir.resolve())
        except (OSError, PermissionError) as fallback_exc:
            logger.warning(
                "Could not create fallback temporary storage directory: %s. "
                "Application startup will proceed, but local file uploads will fail until writable storage is configured.",
                fallback_exc,
            )


    # Initialize database tables (idempotent, ensures tables exist in PostgreSQL / Neon and SQLite)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as exc:
        logger.warning("Database schema initialization encountered: %s", exc)


    # Seed demo account ONLY in non-production environments when explicitly enabled
    if settings.ENVIRONMENT != "production" and settings.ENABLE_DEV_SEEDS:
        try:

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
                    logger.info("[DEV ONLY] Seeded development user: demo@example.org")
        except Exception as exc:
            logger.warning("Could not complete dev seed user creation: %s", exc)


    yield

    logger.info("Shutting down %s...", settings.APP_NAME)
    await engine.dispose()
