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

        # 2. Add Discovery Leads (Filtered)
        for lead in leads:
            if lead.id not in seen_node_ids:
                # Disqualify dates and noise domains from lead nodes if any slipped through
                if lead.lead_type == "date" or is_noise_domain(lead.lead_value):
                    continue

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

        # 3. Add Collapsed & Deduplicated Extracted Entities
        # Key: (entity_type, normalized_value) -> canonical node ID
        canonical_map: dict[tuple[str, str], str] = {}
        entity_id_to_canonical: dict[str, str] = {}
        entity_counts: dict[str, int] = {}

        for ent in entities:
            # Filter noise dates and generic domains out of default knowledge graph
            if ent.entity_type == "date":
                continue
            if ent.entity_type == "domain" and is_noise_domain(ent.normalized_value):
                continue

            entity_key = (ent.entity_type, ent.normalized_value)
            canonical_id = f"ent:{ent.entity_type}:{ent.normalized_value}"
            entity_id_to_canonical[ent.id] = canonical_id

            if entity_key in canonical_map:
                entity_counts[canonical_id] = entity_counts.get(canonical_id, 1) + 1
                continue

            canonical_map[entity_key] = canonical_id
            entity_counts[canonical_id] = 1

            if canonical_id not in seen_node_ids:
                nodes.append(
                    GraphNode(
                        id=canonical_id,
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
                seen_node_ids.add(canonical_id)

                # Traceable relational edge to root
                rel_label = {
                    "domain": "associated_domain",
                    "organization": "affiliated_org",
                    "email": "contact_email",
                    "identifier": "identifier_of",
                }.get(ent.entity_type, "mentions")

                edge_key = (root_id, canonical_id, rel_label)
                if edge_key not in seen_edge_keys:
                    edges.append(
                        GraphEdge(
                            id=f"edge:{root_id}->{canonical_id}",
                            source=root_id,
                            target=canonical_id,
                            label=rel_label,
                            confidence=ent.confidence,
                        )
                    )
                    seen_edge_keys.add(edge_key)

        # Update metadata for occurrences on deduplicated nodes
        for node in nodes:
            if node.id in entity_counts:
                node.metadata["corroboration_count"] = entity_counts[node.id]

        # 4. Map Entity Relationships using Canonical IDs
        for rel in relationships:
            src_canonical = entity_id_to_canonical.get(rel.source_entity_id)
            tgt_canonical = entity_id_to_canonical.get(rel.target_entity_id)
            if src_canonical and tgt_canonical and src_canonical in seen_node_ids and tgt_canonical in seen_node_ids:
                if src_canonical != tgt_canonical:
                    edge_key = (src_canonical, tgt_canonical, rel.relationship_type)
                    if edge_key not in seen_edge_keys:
                        edges.append(
                            GraphEdge(
                                id=f"edge:{src_canonical}->{tgt_canonical}",
                                source=src_canonical,
                                target=tgt_canonical,
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

