"""
Report Generation Service.
Compiles discovered evidence, source documents, entities, and lineage into structured reports.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.db.models.investigation import Investigation, ReportExport
from recursive_osint.db.repositories.evidence_repo import EvidenceRepository
from recursive_osint.db.repositories.investigation_repo import InvestigationRepository
from recursive_osint.schemas.evidence import InvestigationReportResponse


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.evidence_repo = EvidenceRepository(session)
        self.inv_repo = InvestigationRepository(session)

    async def generate_report(self, investigation: Investigation) -> InvestigationReportResponse:
        evidence_list = await self.evidence_repo.list_by_investigation(investigation.id)
        docs_list = await self.evidence_repo.list_documents(investigation.id)
        entities_list = await self.evidence_repo.list_entities(investigation.id)

        # Separate verified evidence from simulated / mock demo records
        real_evidence = [e for e in evidence_list if not getattr(e, "is_simulated", False)]
        simulated_evidence = [e for e in evidence_list if getattr(e, "is_simulated", False)]
        real_docs = [d for d in docs_list if d.connector_name not in ("mock_demo", "mock")]
        simulated_docs = [d for d in docs_list if d.connector_name in ("mock_demo", "mock")]

        # Build Markdown report
        lines = [
            f"# OSINT Investigation Report: {investigation.title}",
            f"**Target Clue:** `{investigation.target_clue}` ({investigation.clue_type})",
            f"**Status:** {investigation.status.upper()} | **Max Depth:** {investigation.max_depth} | **Reached Depth:** {investigation.current_depth}",
            f"**Stop Reason:** {investigation.stop_reason or 'In progress'}",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "",
            "## 1. Executive Summary & Verification Notice",
            "> [!IMPORTANT]",
            "> All source statements are cited directly from public web data. Identity correlations and entity links are probabilistic system inferences and require human corroboration before establishing conclusive identity claims.",
            "",
            f"Verified Sources: **{len(real_docs)}** | Verified Evidence Records: **{len(real_evidence)}** | Extracted Entities: **{len(entities_list)}**",
        ]

        if simulated_evidence:
            lines.extend([
                "",
                "> [!WARNING]",
                f"> **Simulated Data Notice**: {len(simulated_evidence)} mock demo records exist in this dossier. They are labeled UNVERIFIED and excluded from verified evidence counts and executive conclusions.",
            ])

        lines.extend([
            "",
            "## 2. Key Verified Evidence & Supporting Passages",
        ])

        if not real_evidence:
            lines.append("_No verified evidence records captured for this investigation._")
        else:
            for idx, ev in enumerate(real_evidence[:15], 1):
                source_link = f"[{ev.source_url}]({ev.source_url})" if ev.source_url else "N/A"
                conn_name = ev.connector_name or "unknown"
                lines.extend([
                    f"### {idx}. {ev.title}",
                    f"- **Source:** {conn_name.upper()} | **URL:** {source_link}",
                    f"- **Heuristic Confidence:** `{ev.confidence_level.upper()}` (Relevance: {ev.relevance_score:.2f}, Uncertainty: {ev.uncertainty_score:.2f})",
                    f"- **Verification Status:** `{ev.source_verification_status.upper()}`",
                    f"- **Inclusion Rationale:** {ev.why_included}",
                    f"- **Passage:**",
                    f"  > \"{ev.extracted_passage}\"",
                    "",
                ])

        lines.extend([
            "## 3. Discovered Entities & Cross-References",
        ])

        if not entities_list:
            lines.append("_No discrete entities extracted._")
        else:
            lines.append("| Type | Entity Value | Confidence | Context Snippet |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for ent in entities_list[:25]:
                snippet = (ent.context_snippet or "").replace("|", "-")
                lines.append(f"| `{ent.entity_type}` | **{ent.entity_value}** | {ent.confidence:.2f} | {snippet[:80]} |")

        lines.extend([
            "",
            "## 4. Discovered Sources & Provenance",
        ])
        for doc in real_docs[:20]:
            lines.append(f"- [{doc.title}]({doc.url}) — *Connector: {doc.connector_name}* (Retrieved: {doc.retrieved_at.strftime('%Y-%m-%d')})")

        if simulated_docs:
            lines.extend([
                "",
                "## 5. Simulated / Demo Sources (Isolated)",
            ])
            for doc in simulated_docs[:10]:
                lines.append(f"- [MOCK] {doc.title} — *Source: {doc.connector_name}* (Excluded from real conclusions)")

        report_markdown = "\n".join(lines)

        # Save Report Export record
        report_export = ReportExport(
            investigation_id=investigation.id,
            format="markdown",
            content=report_markdown,
            summary_json={
                "sources_scanned": len(docs_list),
                "evidence_count": len(evidence_list),
                "entity_count": len(entities_list),
            },
        )
        self.session.add(report_export)
        await self.session.commit()

        return InvestigationReportResponse(
            investigation_id=investigation.id,
            title=investigation.title,
            target_clue=investigation.target_clue,
            status=investigation.status,
            summary_markdown=report_markdown,
            total_sources_scanned=len(docs_list),
            total_evidence_collected=len(evidence_list),
            total_entities_correlated=len(entities_list),
            generated_at=datetime.now(timezone.utc),
        )
