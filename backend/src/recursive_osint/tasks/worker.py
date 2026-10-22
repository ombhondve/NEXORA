"""
Autonomous Background Investigation Worker Process.
Decouples long-running recursive discovery jobs from the web API process.
"""

import asyncio
import signal
import sys
import time
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.config import settings
from recursive_osint.core.logging import get_logger, setup_logging
from recursive_osint.db.session import AsyncSessionLocal
from recursive_osint.db.models.investigation import Investigation
from recursive_osint.discovery.controller import RecursiveDiscoveryEngine

logger = get_logger("worker")


class InvestigationWorker:
    """Dedicated background worker consuming pending investigation jobs."""

    def __init__(self, poll_interval_seconds: float = 2.0):
        self.poll_interval = poll_interval_seconds
        self.running = False
        self._current_engine: Optional[RecursiveDiscoveryEngine] = None

    def stop(self):
        logger.info("Worker received shutdown signal. Stopping...")
        self.running = False
        if self._current_engine:
            self._current_engine.cancel()

    async def fetch_next_pending_job(self, session: AsyncSession) -> Optional[Investigation]:
        stmt = (
            select(Investigation)
            .where(Investigation.status == "pending")
            .order_by(Investigation.created_at.asc())
            .limit(1)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def run(self):
        setup_logging()
        logger.info("Starting NEXORA Investigation Worker (Poll Interval: %.1fs)...", self.poll_interval)
        self.running = True

        while self.running:
            try:
                async with AsyncSessionLocal() as session:
                    job = await self.fetch_next_pending_job(session)
                    if job:
                        logger.info("Picked up investigation %s ('%s')", job.id, job.title)
                        self._current_engine = RecursiveDiscoveryEngine(session, job)
                        try:
                            await self._current_engine.execute()
                        finally:
                            self._current_engine = None
                    else:
                        await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error("Error in worker execution loop: %s", str(e), exc_info=True)
                await asyncio.sleep(self.poll_interval)

        logger.info("Worker gracefully halted.")


def main():
    worker = InvestigationWorker()

    def handle_sig(sig, frame):
        worker.stop()

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    asyncio.run(worker.run())


if __name__ == "__main__":
    main()
