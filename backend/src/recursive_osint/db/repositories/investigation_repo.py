"""
Investigation and Event repository.
"""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from recursive_osint.db.models.investigation import Investigation, InvestigationEvent, ReportExport
from recursive_osint.db.models.lead_and_query import SearchQuery, DiscoveryLead
from recursive_osint.db.repositories.base import BaseRepository


class InvestigationRepository(BaseRepository[Investigation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Investigation, session)

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Investigation]:
        stmt = (
            select(Investigation)
            .where(Investigation.user_id == user_id)
            .order_by(desc(Investigation.created_at))
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_with_events(self, investigation_id: str) -> Optional[Investigation]:
        stmt = select(Investigation).where(Investigation.id == investigation_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def add_event(self, event: InvestigationEvent) -> InvestigationEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_events(self, investigation_id: str, limit: int = 100) -> List[InvestigationEvent]:
        stmt = (
            select(InvestigationEvent)
            .where(InvestigationEvent.investigation_id == investigation_id)
            .order_by(desc(InvestigationEvent.created_at))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_queries(self, investigation_id: str) -> List[SearchQuery]:
        stmt = (
            select(SearchQuery)
            .where(SearchQuery.investigation_id == investigation_id)
            .order_by(desc(SearchQuery.created_at))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_leads(self, investigation_id: str) -> List[DiscoveryLead]:
        stmt = (
            select(DiscoveryLead)
            .where(DiscoveryLead.investigation_id == investigation_id)
            .order_by(desc(DiscoveryLead.priority_score))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
