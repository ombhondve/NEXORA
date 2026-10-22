"""
Evidence, Document, and Entity repository.
"""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from recursive_osint.db.models.evidence_and_document import EvidenceRecord, SourceDocument
from recursive_osint.db.models.entity import ExtractedEntity, EntityRelationship
from recursive_osint.db.repositories.base import BaseRepository


class EvidenceRepository(BaseRepository[EvidenceRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(EvidenceRecord, session)

    async def list_by_investigation(
        self, investigation_id: str, skip: int = 0, limit: int = 100
    ) -> List[EvidenceRecord]:
        stmt = (
            select(EvidenceRecord)
            .options(selectinload(EvidenceRecord.document))
            .where(EvidenceRecord.investigation_id == investigation_id)
            .order_by(desc(EvidenceRecord.relevance_score))
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_documents(
        self, investigation_id: str, skip: int = 0, limit: int = 100
    ) -> List[SourceDocument]:
        stmt = (
            select(SourceDocument)
            .where(SourceDocument.investigation_id == investigation_id)
            .order_by(desc(SourceDocument.retrieved_at))
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def find_document_by_content_hash(
        self, investigation_id: str, content_hash: str
    ) -> Optional[SourceDocument]:
        stmt = (
            select(SourceDocument)
            .where(
                SourceDocument.investigation_id == investigation_id,
                SourceDocument.content_hash == content_hash,
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_entities(
        self, investigation_id: str, skip: int = 0, limit: int = 200
    ) -> List[ExtractedEntity]:
        stmt = (
            select(ExtractedEntity)
            .where(ExtractedEntity.investigation_id == investigation_id)
            .order_by(desc(ExtractedEntity.confidence))
            .offset(skip)
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_entity_relationships(
        self, investigation_id: str
    ) -> List[EntityRelationship]:
        stmt = (
            select(EntityRelationship)
            .where(EntityRelationship.investigation_id == investigation_id)
            .order_by(desc(EntityRelationship.confidence))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
