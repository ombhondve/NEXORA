"""
Investigation Service.
Manages lifecycle of investigations, dispatching discovery runs, and query logs.
"""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.core.exceptions import EntityNotFoundError, SecurityException, AccessDeniedError
from recursive_osint.db.models.investigation import Investigation, InvestigationEvent
from recursive_osint.db.models.ai_analysis import InvestigationAIAnalysis
from recursive_osint.db.repositories.investigation_repo import InvestigationRepository
from recursive_osint.db.repositories.evidence_repo import EvidenceRepository
from recursive_osint.discovery.controller import RecursiveDiscoveryEngine
from recursive_osint.extraction.entities import is_noise_domain
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
        documents = await evidence_repo.list_documents(investigation_id, limit=300)
        doc_map = {d.id: d for d in documents}
        evidence_items = await evidence_repo.list_by_investigation(investigation_id, limit=300)
        ev_by_doc = {e.document_id: e for e in evidence_items if e.document_id}

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
                metadata={"title": inv.title, "clue_type": inv.clue_type, "relationship_kind": "root"},
            )
        )
        seen_node_ids.add(root_id)

        # 2. Add Discovery Leads (Filtered)
        for lead in leads:
            if lead.id not in seen_node_ids:
                # Disqualify dates and noise domains from lead nodes if any slipped through
                if lead.lead_type == "date" or is_noise_domain(lead.lead_value):
                    continue

                rel_kind = "direct" if lead.depth <= 1 else "inferred"
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
                            "relationship_kind": rel_kind,
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
                            relationship_kind=rel_kind,
                            confidence_rationale=lead.discovery_reason or f"Autonomous lead expansion at depth {lead.depth}",
                        )
                    )
                    seen_edge_keys.add(edge_key)

        # 3. Add Collapsed & Deduplicated Extracted Entities with Document Provenance
        # Key: (entity_type, normalized_value) -> canonical node ID
        canonical_map: dict[tuple[str, str], str] = {}
        entity_id_to_canonical: dict[str, str] = {}
        entity_counts: dict[str, int] = {}
        canonical_doc_ids: dict[str, str] = {}

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
            if ent.document_id:
                canonical_doc_ids[canonical_id] = ent.document_id

            if canonical_id not in seen_node_ids:
                doc = doc_map.get(ent.document_id) if ent.document_id else None
                ev = ev_by_doc.get(ent.document_id) if ent.document_id else None
                is_simulated = bool(doc and doc.connector_name in ("mock_demo", "mock"))
                rel_kind = "unverified" if is_simulated else ("direct" if ent.confidence >= 0.8 else "inferred")

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
                            "source_url": doc.url if doc else None,
                            "source_title": doc.title if doc else None,
                            "connector_name": doc.connector_name if doc else None,
                            "relationship_kind": rel_kind,
                            "is_simulated": is_simulated,
                            "evidence_excerpt": ev.extracted_passage if ev else ent.context_snippet,
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
                            relationship_kind=rel_kind,
                            evidence_id=ev.id if ev else None,
                            evidence_title=doc.title if doc else None,
                            source_url=doc.url if doc else None,
                            confidence_rationale=(
                                f"Extracted from {doc.title} ({doc.connector_name})"
                                if doc else f"Entity cross-reference with target"
                            ),
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
                                relationship_kind="inferred",
                                confidence_rationale=rel.provenance_notes or "Correlated relationship across documents",
                                origin="deterministic",
                            )
                        )
                        seen_edge_keys.add(edge_key)

        # 5. Integrate AI-Generated Contextual Relationship Candidates
        try:
            stmt = (
                select(InvestigationAIAnalysis)
                .where(InvestigationAIAnalysis.investigation_id == investigation_id)
                .order_by(desc(InvestigationAIAnalysis.created_at))
                .limit(1)
            )
            ai_res = await self.session.execute(stmt)
            latest_ai = ai_res.scalar_one_or_none()
            if latest_ai and latest_ai.relationships_json:
                # Build canonical lookup mapping node IDs, labels, and normalized values
                node_lookup: dict[str, str] = {}
                for node in nodes:
                    node_lookup[node.id.lower()] = node.id
                    node_lookup[node.label.strip().lower()] = node.id
                    if "normalized_value" in node.metadata:
                        node_lookup[str(node.metadata["normalized_value"]).strip().lower()] = node.id

                evidence_id_set = {e.id for e in evidence_items}
                ev_map_by_id = {e.id: e for e in evidence_items}

                for ai_rel in latest_ai.relationships_json:
                    src_raw = str(ai_rel.get("source_entity", "")).strip().lower()
                    tgt_raw = str(ai_rel.get("target_entity", "")).strip().lower()
                    rel_type = str(ai_rel.get("relationship_type", "associated_with")).strip()
                    explanation = str(ai_rel.get("explanation", "AI contextual correlation")).strip()
                    raw_confidence = ai_rel.get("confidence", 0.65)
                    try:
                        confidence = max(0.0, min(1.0, float(raw_confidence)))
                    except (ValueError, TypeError):
                        confidence = 0.65

                    # Resolve to actual canonical node IDs
                    src_node_id = node_lookup.get(src_raw)
                    tgt_node_id = node_lookup.get(tgt_raw)

                    # Strictly verify that endpoints resolve to existent canonical graph nodes
                    if not src_node_id or not tgt_node_id or src_node_id not in seen_node_ids or tgt_node_id not in seen_node_ids:
                        continue
                    if src_node_id == tgt_node_id:
                        continue

                    # Validate AI relationship evidence citations against actual investigation evidence
                    raw_ev_ids = ai_rel.get("evidence_ids", [])
                    valid_ev_ids = [eid for eid in raw_ev_ids if eid in evidence_id_set] if isinstance(raw_ev_ids, list) else []
                    primary_ev_id = valid_ev_ids[0] if valid_ev_ids else None
                    primary_ev = ev_map_by_id.get(primary_ev_id) if primary_ev_id else None

                    # Do not treat AI relationship as directly verified purely based on high confidence
                    raw_kind = str(ai_rel.get("relationship_kind", "inferred")).lower().strip()
                    if raw_kind == "direct" and not (primary_ev and getattr(primary_ev, "is_verified_source_statement", False)):
                        rel_kind = "inferred"
                    elif raw_kind in ("direct", "inferred", "unverified"):
                        rel_kind = raw_kind
                    else:
                        rel_kind = "inferred"

                    # Edge deduplication: do not duplicate overlapping deterministic or existing edges
                    edge_key = (src_node_id, tgt_node_id, rel_type)
                    reverse_key = (tgt_node_id, src_node_id, rel_type)
                    if edge_key not in seen_edge_keys and reverse_key not in seen_edge_keys:
                        # Extract source URL and title from referenced evidence record
                        source_doc = doc_map.get(primary_ev.document_id) if primary_ev and primary_ev.document_id else None
                        source_url = source_doc.url if source_doc else getattr(primary_ev, "source_url", None)
                        evidence_title = primary_ev.title if primary_ev else (source_doc.title if source_doc else None)

                        edges.append(
                            GraphEdge(
                                id=f"ai_edge:{src_node_id}->{tgt_node_id}:{rel_type}",
                                source=src_node_id,
                                target=tgt_node_id,
                                label=rel_type,
                                confidence=confidence,
                                relationship_kind=rel_kind,
                                evidence_id=primary_ev_id,
                                evidence_title=evidence_title,
                                source_url=source_url,
                                confidence_rationale=f"AI Inferred ({confidence * 100:.0f}%): {explanation}",
                                origin="ai_inferred",
                            )
                        )
                        seen_edge_keys.add(edge_key)
        except Exception:
            pass  # Fail gracefully without blocking deterministic graph

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

