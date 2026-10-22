"""
Demo Data Seeding Script.
Populates an end-to-end investigation with realistic multi-source findings,
correlated evidence, extracted entities, and synthesized report.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

import asyncio
from recursive_osint.db.session import AsyncSessionLocal
from recursive_osint.db.models.user import User
from recursive_osint.db.models.investigation import Investigation, InvestigationEvent, ReportExport
from recursive_osint.db.models.evidence_and_document import SourceDocument, EvidenceRecord
from recursive_osint.db.models.entity import ExtractedEntity
from recursive_osint.search.deduplication import canonicalize_url, compute_content_hash
from recursive_osint.services.report_service import ReportService


async def seed_demo():
    print("[*] Seeding realistic demonstration investigation...")
    async with AsyncSessionLocal() as session:
        from recursive_osint.db.repositories.user_repo import UserRepository
        repo = UserRepository(session)
        user = await repo.get_by_email("demo@example.org")
        if not user:
            print("[!] Run scripts/setup-dev.py first to create the demo user.")
            return

        # Create sample investigation
        inv = Investigation(
            user_id=user.id,
            title="Operation Meridian: Global Cyber Infrastructure",
            description="Autonomous recursive discovery across public registry datasets, research papers, and archived network infrastructure.",
            target_clue="NEXORA Cyber Operations",
            clue_type="text",
            status="completed",
            max_depth=3,
            current_depth=3,
            max_total_queries=20,
            progress_percent=100,
            stop_reason="Lead discovery completed within allotted budget.",
        )
        session.add(inv)
        await session.flush()

        # Add Events
        events = [
            ("investigation_started", "Autonomous discovery initiated for clue: NEXORA Cyber Operations"),
            ("query_executed", "Searched Wikipedia Open Knowledge for 'NEXORA Cyber Operations'"),
            ("doc_fetched", "Discovered official public record at registry.example.org"),
            ("entity_extracted", "Extracted domain: portal.nexora-defense.org (Confidence: 85%)"),
            ("lead_discovered", "Discovered new recursive lead [domain]: 'portal.nexora-defense.org' at depth 1"),
            ("query_executed", "Searched Internet Archive Historical Data for 'portal.nexora-defense.org'"),
            ("investigation_completed", "Investigation finalized. Stop reason: Lead discovery completed within allotted budget."),
        ]
        for e_type, msg in events:
            session.add(
                InvestigationEvent(
                    investigation_id=inv.id,
                    event_type=e_type,
                    message=msg,
                )
            )

        # Add Source Documents
        doc1 = SourceDocument(
            investigation_id=inv.id,
            connector_name="wikipedia",
            title="Sovereign Digital Infrastructure Consortium Overview",
            url="https://en.wikipedia.org/wiki/Sovereign_Digital_Infrastructure",
            canonical_url="https://en.wikipedia.org/wiki/sovereign_digital_infrastructure",
            content_hash=compute_content_hash("Sovereign Digital Infrastructure Consortium Overview"),
            snippet="The alliance maintains decentralized verification nodes across Western Europe and coordinates with the NEXORA Cyber Operations group on open telemetry standards.",
            publication_date="2024-02-18",
        )
        doc2 = SourceDocument(
            investigation_id=inv.id,
            connector_name="open_datasets",
            title="Analysis of Autonomous Threat Reconnaissance Protocols",
            url="https://doi.org/10.1007/s10207-024-00812-1",
            canonical_url="https://doi.org/10.1007/s10207-024-00812-1",
            content_hash=compute_content_hash("Analysis of Autonomous Threat Reconnaissance Protocols"),
            snippet="Technical evaluation of recursive graph correlation methodologies citing Dr. H. Vance and contact infrastructure admin@nexora-defense.org.",
            publication_date="2024-05-12",
        )
        session.add_all([doc1, doc2])
        await session.flush()

        # Add Evidence Records
        ev1 = EvidenceRecord(
            investigation_id=inv.id,
            document_id=doc1.id,
            title="Formal Affiliation with NEXORA Operations",
            extracted_passage="coordinates with the NEXORA Cyber Operations group on open telemetry standards.",
            relevance_score=0.92,
            uncertainty_score=0.12,
            confidence_level="high",
            why_included="Verbatim match of target entity in verified encyclopedic database.",
        )
        ev2 = EvidenceRecord(
            investigation_id=inv.id,
            document_id=doc2.id,
            title="Technical Contact & Protocol Correlation",
            extracted_passage="citing Dr. H. Vance and contact infrastructure admin@nexora-defense.org.",
            relevance_score=0.84,
            uncertainty_score=0.25,
            confidence_level="medium",
            why_included="Identifies key researcher and institutional contact email for target infrastructure.",
        )
        session.add_all([ev1, ev2])

        # Add Extracted Entities
        entities = [
            ExtractedEntity(
                investigation_id=inv.id,
                document_id=doc1.id,
                entity_type="organization",
                entity_value="Sovereign Digital Infrastructure",
                normalized_value="sovereign digital infrastructure",
                confidence=0.90,
                context_snippet="The alliance maintains decentralized nodes...",
            ),
            ExtractedEntity(
                investigation_id=inv.id,
                document_id=doc2.id,
                entity_type="domain",
                entity_value="nexora-defense.org",
                normalized_value="nexora-defense.org",
                confidence=0.95,
                context_snippet="contact infrastructure admin@nexora-defense.org",
            ),
            ExtractedEntity(
                investigation_id=inv.id,
                document_id=doc2.id,
                entity_type="email",
                entity_value="admin@nexora-defense.org",
                normalized_value="admin@nexora-defense.org",
                confidence=0.88,
                context_snippet="citing Dr. H. Vance and contact infrastructure admin@nexora-defense.org",
            ),
        ]
        session.add_all(entities)
        await session.commit()

        # Generate Report
        rep_service = ReportService(session)
        await rep_service.generate_report(inv)

        print(f"[SUCCESS] Seeded demonstration investigation (ID: {inv.id}) with documents, evidence, and report!")


if __name__ == "__main__":
    asyncio.run(seed_demo())
