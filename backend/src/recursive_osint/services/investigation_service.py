"""
Investigation Service.
Manages lifecycle of investigations, dispatching discovery runs, and query logs.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.core.exceptions import EntityNotFoundError, SecurityException, AccessDeniedError
from recursive_osint.db.models.investigation import Investigation, InvestigationEvent
from recursive_osint.db.repositories.investigation_repo import InvestigationRepository
from recursive_osint.discovery.controller import RecursiveDiscoveryEngine
from recursive_osint.schemas.investigation import InvestigationCreate, InvestigationUpdate


class InvestigationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = InvestigationRepository(session)

    async def create_investigation(self, user_id: Optional[str], data: InvestigationCreate) -> Investigation:
        investigation = Investigation(
            user_id=user_id,
            title=data.title,
            description=data.description,
            target_clue=data.target_clue,
            clue_type=data.clue_type,
            max_depth=data.max_depth,
            max_total_queries=data.max_total_queries,
            max_execution_seconds=data.max_execution_seconds,
            status="pending",
        )
        created = await self.repo.create(investigation)
        # Emit initial created event
        await self.repo.add_event(
            InvestigationEvent(
                investigation_id=created.id,
                event_type="investigation_created",
                message=f"Investigation created for clue '{data.target_clue}'",
                details_json={"clue_type": data.clue_type, "max_depth": data.max_depth},
            )
        )
        return created

    async def get_investigation(self, investigation_id: str, user_id: Optional[str] = None) -> Investigation:
        inv = await self.repo.get_by_id(investigation_id)
        if not inv:
            raise EntityNotFoundError(f"Investigation {investigation_id} not found.")
        # If user_id is provided and the investigation has an owner, verify ownership
        if user_id and inv.user_id and inv.user_id != user_id:
            raise AccessDeniedError("Access to this investigation is restricted to its owner.")
        return inv

    async def list_user_investigations(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Investigation]:
        return await self.repo.list_by_user(user_id, skip=skip, limit=limit)

    async def start_discovery(self, investigation_id: str, user_id: Optional[str] = None) -> Investigation:
        inv = await self.get_investigation(investigation_id, user_id)
        engine = RecursiveDiscoveryEngine(self.session, inv)
        return await engine.execute()

    async def cancel_discovery(self, investigation_id: str, user_id: Optional[str] = None) -> Investigation:
        inv = await self.get_investigation(investigation_id, user_id)
        inv.status = "cancelled"
        inv.stop_reason = "Cancelled by user request."
        await self.repo.add_event(
            InvestigationEvent(
                investigation_id=inv.id,
                event_type="investigation_cancelled",
                message="Investigation cancelled by user request.",
            )
        )
        await self.session.commit()
        return inv

    async def get_events(self, investigation_id: str, user_id: Optional[str] = None) -> List[InvestigationEvent]:
        await self.get_investigation(investigation_id, user_id)
        return await self.repo.get_events(investigation_id)

