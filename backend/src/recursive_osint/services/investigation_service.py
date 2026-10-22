"""
Investigation Service.
Manages lifecycle of investigations, dispatching discovery runs, and query logs.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.core.exceptions import EntityNotFoundError, SecurityException, AccessDeniedError
from recursive_osint.db.models.investigation import Investigation, InvestigationEvent
from recursive_osint.db.repositories.investigation_repo import InvestigationRepository
from recursive_osint.db.repositories.evidence_repo import EvidenceRepository
from recursive_osint.discovery.controller import RecursiveDiscoveryEngine
from recursive_osint.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
    LeadGraphResponse,
    GraphNode,
    GraphEdge,
)


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

    async def get_lead_graph(self, investigation_id: str, user_id: Optional[str] = None) -> LeadGraphResponse:
        inv = await self.get_investigation(investigation_id, user_id)
        leads = await self.repo.get_leads(investigation_id)

        evidence_repo = EvidenceRepository(self.session)
        entities = await evidence_repo.list_entities(investigation_id)
        relationships = await evidence_repo.list_entity_relationships(investigation_id)

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        seen_node_ids: set[str] = set()
        seen_edge_keys: set[tuple[str, str, str]] = set()

        # 1. Root seed node
        root_id = f"seed:{inv.id}"
        nodes.append(
            GraphNode(
                id=root_id,
                label=inv.target_clue,
                type="seed",
                depth=0,
                status="root",
                metadata={"title": inv.title, "clue_type": inv.clue_type},
            )
        )
        seen_node_ids.add(root_id)

        # 2. Add Discovery Leads
        for lead in leads:
            if lead.id not in seen_node_ids:
                nodes.append(
                    GraphNode(
                        id=lead.id,
                        label=lead.lead_value,
                        type=lead.lead_type,
                        depth=lead.depth,
                        status=lead.status,
                        confidence=lead.priority_score,
                        metadata={
                            "discovery_reason": lead.discovery_reason,
                            "priority_score": lead.priority_score,
                        },
                    )
                )
                seen_node_ids.add(lead.id)

            # Determine parent connection safely
            parent_id = (
                lead.parent_lead_id
                if (lead.parent_lead_id and lead.parent_lead_id in seen_node_ids)
                else root_id
            )
            edge_key = (parent_id, lead.id, "expanded_to")
            if edge_key not in seen_edge_keys:
                edges.append(
                    GraphEdge(
                        id=f"edge:{parent_id}->{lead.id}",
                        source=parent_id,
                        target=lead.id,
                        label="expanded_to",
                        confidence=lead.priority_score,
                    )
                )
                seen_edge_keys.add(edge_key)

        # 3. Add Extracted Entities and Relationships
        for ent in entities:
            ent_id = f"ent:{ent.id}"
            if ent_id not in seen_node_ids:
                nodes.append(
                    GraphNode(
                        id=ent_id,
                        label=ent.entity_value,
                        type=ent.entity_type,
                        depth=1,
                        status="extracted",
                        confidence=ent.confidence,
                        metadata={
                            "normalized_value": ent.normalized_value,
                            "context": ent.context_snippet,
                        },
                    )
                )
                seen_node_ids.add(ent_id)

                # Connect to root
                edge_key = (root_id, ent_id, "mentions")
                if edge_key not in seen_edge_keys:
                    edges.append(
                        GraphEdge(
                            id=f"edge:{root_id}->{ent_id}",
                            source=root_id,
                            target=ent_id,
                            label="mentions",
                            confidence=ent.confidence,
                        )
                    )
                    seen_edge_keys.add(edge_key)

        for rel in relationships:
            src_id = f"ent:{rel.source_entity_id}"
            tgt_id = f"ent:{rel.target_entity_id}"
            if src_id in seen_node_ids and tgt_id in seen_node_ids:
                edge_key = (src_id, tgt_id, rel.relationship_type)
                if edge_key not in seen_edge_keys:
                    edges.append(
                        GraphEdge(
                            id=f"edge:{src_id}->{tgt_id}",
                            source=src_id,
                            target=tgt_id,
                            label=rel.relationship_type,
                            confidence=rel.confidence,
                        )
                    )
                    seen_edge_keys.add(edge_key)

        is_empty = len(nodes) <= 1 and len(edges) == 0

        return LeadGraphResponse(
            investigation_id=inv.id,
            target_clue=inv.target_clue,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
            is_empty=is_empty,
        )

