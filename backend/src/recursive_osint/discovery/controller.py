"""
Recursive OSINT Discovery Controller.
Orchestrates autonomous recursive discovery, lead priority expansion, deduplication,
evidence evaluation, and budget enforcement.
"""

import asyncio
import time
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.connectors.registry import connector_registry
from recursive_osint.core.logging import get_logger
from recursive_osint.db.models.investigation import Investigation, InvestigationEvent
from recursive_osint.db.models.lead_and_query import SearchQuery, DiscoveryLead
from recursive_osint.db.models.evidence_and_document import SourceDocument, EvidenceRecord
from recursive_osint.db.models.entity import ExtractedEntity, EntityRelationship
from recursive_osint.discovery.budget import InvestigationBudget
from recursive_osint.discovery.lead_queue import LeadPriorityQueue
from recursive_osint.discovery.stopping_rules import StoppingRules
from recursive_osint.evidence.relevance import EvidenceEvaluator
from recursive_osint.extraction.entities import EntityExtractor
from recursive_osint.search.deduplication import canonicalize_url, compute_content_hash
from recursive_osint.search.query_expansion import QueryExpansionEngine

logger = get_logger("discovery.controller")


class RecursiveDiscoveryEngine:
    """Central engine executing the recursive multi-source OSINT discovery workflow."""

    def __init__(self, session: AsyncSession, investigation: Investigation):
        self.session = session
        self.investigation = investigation
        self.budget = InvestigationBudget(
            max_depth=investigation.max_depth,
            max_total_queries=investigation.max_total_queries,
            max_execution_seconds=investigation.max_execution_seconds,
        )
        self.queue = LeadPriorityQueue()
        self.is_cancelled = False
        self.consecutive_zero_results = 0

    async def emit_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Records an auditable event in the investigation log."""
        event = InvestigationEvent(
            investigation_id=self.investigation.id,
            event_type=event_type,
            message=message,
            details_json=details or {},
        )
        self.session.add(event)
        await self.session.flush()

    async def execute(self) -> Investigation:
        """Executes the full recursive discovery cycle."""
        logger.info("Starting recursive investigation %s for clue '%s'", self.investigation.id, self.investigation.target_clue)

        self.investigation.status = "running"
        await self.emit_event("investigation_started", f"Autonomous discovery initiated for clue: {self.investigation.target_clue}")

        # Seed initial root lead
        root_lead = DiscoveryLead(
            investigation_id=self.investigation.id,
            lead_type=self.investigation.clue_type,
            lead_value=self.investigation.target_clue,
            depth=0,
            priority_score=1.0,
            status="evaluating",
            discovery_reason="Initial seed clue provided by investigator.",
        )
        self.session.add(root_lead)
        await self.session.flush()

        self.queue.push(
            lead_id=root_lead.id,
            lead_type=root_lead.lead_type,
            lead_value=root_lead.lead_value,
            depth=root_lead.depth,
            priority_score=root_lead.priority_score,
            discovery_reason=root_lead.discovery_reason,
        )

        stop_reason = ""
        seen_canonical_urls: set[str] = set()

        while not self.queue.is_empty():
            # Check stopping conditions
            should_stop, reason = StoppingRules.evaluate(
                budget=self.budget,
                consecutive_zero_results=self.consecutive_zero_results,
                lead_queue_empty=self.queue.is_empty(),
                is_cancelled=self.is_cancelled,
            )
            if should_stop:
                stop_reason = reason
                break

            lead = self.queue.pop()
            if not lead:
                break

            current_depth = lead.depth
            self.investigation.current_depth = max(self.investigation.current_depth, current_depth)

            # Generate targeted queries for this lead
            if current_depth == 0:
                queries = QueryExpansionEngine.expand_initial_clue(lead.lead_value, lead.lead_type)
            else:
                queries = QueryExpansionEngine.generate_followup_queries(
                    lead.lead_value, lead.lead_type, self.investigation.target_clue
                )

            lead_discovered_any_results = False

            # Execute across active connectors
            active_connectors = connector_registry.list_enabled()
            for query_text in queries:
                if self.budget.queries_executed >= self.budget.max_total_queries:
                    break

                for connector in active_connectors:
                    if self.budget.queries_executed >= self.budget.max_total_queries:
                        break

                    query_start_time = time.perf_counter()
                    query_log = SearchQuery(
                        investigation_id=self.investigation.id,
                        query_text=query_text,
                        source_name=connector.name,
                        depth=current_depth,
                        status="executing",
                    )
                    self.session.add(query_log)
                    await self.session.flush()

                    try:
                        self.budget.record_query()
                        search_results = await connector.search(query_text, max_results=5)
                        duration_ms = (time.perf_counter() - query_start_time) * 1000.0

                        query_log.status = "completed"
                        query_log.results_count = len(search_results)
                        query_log.execution_duration_ms = duration_ms

                        if search_results:
                            lead_discovered_any_results = True
                            await self.emit_event(
                                "query_executed",
                                f"Searched {connector.display_name} for '{query_text}', discovered {len(search_results)} records.",
                                {"source": connector.name, "count": len(search_results), "depth": current_depth},
                            )

                        # Process Discovered Records
                        for item in search_results:
                            canonical_url = canonicalize_url(item.url)
                            content_hash = compute_content_hash(f"{item.title} {item.snippet}")

                            if canonical_url in seen_canonical_urls:
                                continue
                            seen_canonical_urls.add(canonical_url)

                            # Persist Source Document
                            doc = SourceDocument(
                                investigation_id=self.investigation.id,
                                connector_name=connector.name,
                                title=item.title,
                                url=item.url,
                                canonical_url=canonical_url,
                                content_hash=content_hash,
                                snippet=item.snippet,
                                publication_date=item.publication_date,
                            )
                            self.session.add(doc)
                            await self.session.flush()

                            # Evaluate Evidence Relevance & Uncertainty
                            full_passage = f"{item.title}. {item.snippet}"
                            relevance, uncertainty, conf, why = EvidenceEvaluator.evaluate_passage(
                                passage=full_passage,
                                clue=self.investigation.target_clue,
                                source_name=connector.display_name,
                            )

                            evidence = EvidenceRecord(
                                investigation_id=self.investigation.id,
                                document_id=doc.id,
                                title=item.title,
                                extracted_passage=item.snippet,
                                relevance_score=relevance,
                                uncertainty_score=uncertainty,
                                confidence_level=conf,
                                why_included=why,
                            )
                            self.session.add(evidence)

                            # Extract Entities
                            entities = EntityExtractor.extract_all(full_passage)
                            saved_entities: List[ExtractedEntity] = []
                            for e in entities:
                                extracted_ent = ExtractedEntity(
                                    investigation_id=self.investigation.id,
                                    document_id=doc.id,
                                    entity_type=e.entity_type,
                                    entity_value=e.entity_value,
                                    normalized_value=e.normalized_value,
                                    confidence=e.confidence,
                                    context_snippet=e.context_snippet,
                                )
                                self.session.add(extracted_ent)
                                saved_entities.append(extracted_ent)

                                # Push high-confidence entities as new recursive leads if within depth limit
                                next_depth = current_depth + 1
                                if next_depth <= self.budget.max_depth and e.confidence >= 0.75:
                                    child_lead = DiscoveryLead(
                                        investigation_id=self.investigation.id,
                                        parent_lead_id=lead.lead_id,
                                        lead_type=e.entity_type,
                                        lead_value=e.entity_value,
                                        depth=next_depth,
                                        priority_score=e.confidence * (1.0 - (next_depth * 0.15)),
                                        status="queued",
                                        discovery_reason=f"Extracted from {doc.title} ({connector.name})",
                                    )
                                    self.session.add(child_lead)
                                    await self.session.flush()

                                    pushed = self.queue.push(
                                        lead_id=child_lead.id,
                                        lead_type=child_lead.lead_type,
                                        lead_value=child_lead.lead_value,
                                        depth=child_lead.depth,
                                        priority_score=child_lead.priority_score,
                                        discovery_reason=child_lead.discovery_reason,
                                    )
                                    if pushed:
                                        await self.emit_event(
                                            "lead_discovered",
                                            f"Discovered new recursive lead [{e.entity_type}]: '{e.entity_value}' at depth {next_depth}",
                                            {"lead_value": e.entity_value, "depth": next_depth},
                                        )

                        await self.session.flush()

                    except Exception as exc:
                        logger.error("Query failed for connector %s: %s", connector.name, str(exc))
                        query_log.status = "failed"
                        query_log.error_message = str(exc)
                        await self.session.flush()

            if lead_discovered_any_results:
                self.consecutive_zero_results = 0
            else:
                self.consecutive_zero_results += 1

            # Update progress percent based on queries executed vs budget limit
            progress = int((self.budget.queries_executed / self.budget.max_total_queries) * 100)
            self.investigation.progress_percent = min(100, max(self.investigation.progress_percent, progress))
            await self.session.commit()

        # Finalize investigation
        if not stop_reason:
            stop_reason = "Lead discovery completed within allotted budget."

        self.investigation.status = "completed" if not self.is_cancelled else "cancelled"
        self.investigation.stop_reason = stop_reason
        self.investigation.progress_percent = 100
        await self.emit_event("investigation_completed", f"Investigation finalized. Stop reason: {stop_reason}")
        await self.session.commit()

        logger.info("Investigation %s finished with reason: %s", self.investigation.id, stop_reason)
        return self.investigation

    def cancel(self) -> None:
        """Signals the controller to halt recursive expansion immediately."""
        self.is_cancelled = True
