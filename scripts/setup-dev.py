"""
Local Development Setup Script.
Prepares storage directory, verifies configuration, and initializes SQLite/PostgreSQL schema.
"""

import sys
import os
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

import asyncio
from recursive_osint.config import settings
from recursive_osint.db.base import Base
from recursive_osint.db.session import engine, AsyncSessionLocal
from recursive_osint.core.security import hash_password
from recursive_osint.db.models.user import User


async def setup_dev():
    print(f"[*] Initializing {settings.APP_NAME}...")
    print(f"[*] Environment: {settings.ENVIRONMENT}")
    print(f"[*] Database URL: {settings.DATABASE_URL}")

    # Create local storage folders
    storage_path = Path(settings.STORAGE_LOCAL_ROOT)
    storage_path.mkdir(parents=True, exist_ok=True)
    print(f"[+] Storage directory ready at: {storage_path.resolve()}")

    # Initialize tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[+] Database tables successfully initialized.")

    # Seed demo account
    async with AsyncSessionLocal() as session:
        from recursive_osint.db.repositories.user_repo import UserRepository
        repo = UserRepository(session)
        existing = await repo.get_by_email("demo@example.org")
        if not existing:
            demo_user = User(
                email="demo@example.org",
                hashed_password=hash_password("password123"),
                full_name="OSINT Lead Analyst",
                role="investigator",
                is_active=True,
            )
            session.add(demo_user)
            await session.commit()
            print("[+] Seeded demo analyst: demo@example.org (password: password123)")
        else:
            print("[*] Demo analyst account already exists.")

    print("\n[SUCCESS] Local development environment successfully initialized!")


if __name__ == "__main__":
    asyncio.run(setup_dev())
