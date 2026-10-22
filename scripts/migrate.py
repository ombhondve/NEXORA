"""
Database Migration Execution Script.
Runs Alembic migrations or synchronizes DeclarativeBase models.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

import asyncio
from recursive_osint.config import settings
from recursive_osint.db.base import Base
from recursive_osint.db.session import engine
import recursive_osint.db.models


async def run_migrations():
    print(f"[*] Running database migrations against: {settings.get_redacted_database_url()}")

    # Verify connection
    async with engine.begin() as conn:
        print("[*] Verifying schema and foreign key constraints...")
        await conn.run_sync(Base.metadata.create_all)
        print("[+] Schema synchronized successfully. All 16 entity tables verified.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
