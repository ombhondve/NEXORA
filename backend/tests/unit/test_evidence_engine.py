"""
Reliable Evidence Engine Unit and Benchmark Tests.
Verifies Phase 1 Evidence Engine requirements:
- Provenance integrity (source_url, connector_name, retrieval timestamp, verification status)
- Incidental mention down-ranking
- Date and noise domain exclusion from search leads
- Traceable graph edges with evidence references
- Mock demo record isolation from real evidence counts
- Benchmark dataset measuring precision, false-positive rate, and duplicate rate
"""

import uuid
from datetime import datetime, timezone
import pytest
from recursive_osint.db.models.evidence_and_document import SourceDocument, EvidenceRecord
from recursive_osint.extraction.entities import EntityExtractor, is_noise_domain
from recursive_osint.evidence.relevance import EvidenceEvaluator
from recursive_osint.schemas.evidence import EvidenceRecordResponse
from recursive_osint.discovery.budget import InvestigationBudget
from recursive_osint.discovery.stopping_rules import StoppingRules


class TestEvidenceProvenanceIntegrity:
    """Tests Step 2: Full provenance preservation on EvidenceRecord."""

    def test_evidence_inherits_document_provenance_properties(self):
        """EvidenceRecord must expose source_url, connector_name, and verification status from its document."""
        doc = SourceDocument(
            id=str(uuid.uuid4()),
            investigation_id=str(uuid.uuid4()),
            connector_name="openalex",
            title="Empirical Analysis of Cloud Computing Systems",
            url="https://doi.org/10.1145/example.cloud",
            canonical_url="https://doi.org/10.1145/example.cloud",
            content_hash="abc123hash",
            snippet="Published study on cloud infrastructure architecture.",
            publication_date="2023-04-15",
            retrieved_at=datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc),
        )

        evidence = EvidenceRecord(
            id=str(uuid.uuid4()),
            investigation_id=doc.investigation_id,
            document_id=doc.id,
            title="Cloud Infrastructure Finding",
            extracted_passage="Study on cloud infrastructure architecture.",
            relevance_score=0.85,
            uncertainty_score=0.15,
            confidence_level="high",
            why_included="Central topic match in scholarly publication.",
            is_verified_source_statement=True,
        )
        evidence.document = doc

        # Verify provenance properties
        assert evidence.source_url == "https://doi.org/10.1145/example.cloud"
        assert evidence.source_title == "Empirical Analysis of Cloud Computing Systems"
        assert evidence.connector_name == "openalex"
        assert evidence.publication_date == "2023-04-15"
        assert evidence.retrieved_at == datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)
        assert evidence.source_verification_status == "primary"
        assert evidence.is_simulated is False

        # Verify serialization via EvidenceRecordResponse
        response = EvidenceRecordResponse.model_validate(evidence)
        assert response.source_url == doc.url
        assert response.connector_name == "openalex"
        assert response.source_verification_status == "primary"
        assert response.is_simulated is False

    def test_mock_document_is_properly_flagged_as_simulated(self):
        """Mock demo records must be flagged is_simulated=True and status='simulated'."""
        mock_doc = SourceDocument(
            id=str(uuid.uuid4()),
            investigation_id=str(uuid.uuid4()),
            connector_name="mock_demo",
            title="Synthetic Target Finding",
            url="https://example.org/demo-record",
            canonical_url="https://example.org/demo-record",
            content_hash="mockhash",
            snippet="Simulated test finding.",
        )
        evidence = EvidenceRecord(
            id=str(uuid.uuid4()),
            investigation_id=mock_doc.investigation_id,
            document_id=mock_doc.id,
            title="Synthetic Finding",
            extracted_passage="Simulated test finding.",
            relevance_score=0.15,
            uncertainty_score=0.85,
            confidence_level="unverified",
            why_included="[Simulated Source] Demo record.",
            is_verified_source_statement=False,
        )
        evidence.document = mock_doc

        assert evidence.is_simulated is True
        assert evidence.source_verification_status == "simulated"

        response = EvidenceRecordResponse.model_validate(evidence)
        assert response.is_simulated is True
        assert response.source_verification_status == "simulated"


class TestRelevanceAndExtractionFiltering:
    """Tests Step 3 & 4: Relevance calibration and extraction filtering."""

    def test_incidental_and_boilerplate_downranking(self):
        """Mentions of a target in compatibility or navigation contexts must be down-ranked."""
        passage = (
            "This software is compatible with Microsoft Windows. "
            "Terms of use and privacy policy all rights reserved."
        )
        score, conf, why = EvidenceEvaluator.evaluate(
            clue="Microsoft",
            passage=passage,
            source_name="searxng",
            title="Generic Utility Application",
        )
        assert score <= 0.40
        assert conf in ("low", "unverified")
        assert "incidental" in why.lower()

    def test_dates_are_strictly_temporal_attributes(self):
        """Dates extracted from text must have is_lead_candidate=False."""
        text = "Event occurred on 2021-08-12 and updated on 2023-01-15."
        entities = EntityExtractor.extract_all(text)
        dates = [e for e in entities if e.entity_type == "date"]
        assert len(dates) >= 1
        for d in dates:
            assert d.is_lead_candidate is False

    def test_generic_org_exclusions(self):
        """Boilerplate capitalized strings like 'Terms of Service Inc' must be excluded."""
        text = "Contact Terms of Service Inc or Privacy Policy LLC for legal details."
        entities = EntityExtractor.extract_all(text)
        orgs = [e for e in entities if e.entity_type == "organization"]
        assert not any("terms of service" in o.normalized_value for o in orgs)


class TestBenchmarkQualityMetrics:
    """Tests Step 9: Benchmark measuring precision, duplicate rate, and false-positive rate."""

    def test_benchmark_noise_rejection_rate(self):
        """Benchmark dataset of 20 sample domains containing 10 valid infrastructure and 10 noise domains."""
        dataset = [
            # 10 Known Noise / Third-Party Platforms
            ("youtube.com", True),
            ("moodle.org", True),
            ("canvas.instructure.com", True),
            ("twitter.com", True),
            ("facebook.com", True),
            ("linkedin.com", True),
            ("github.io", True),
            ("example.org", True),
            ("schema.org", True),
            ("w3.org", True),
            # 10 Legitimate Investigative Targets / Domains
            ("microsoft.com", False),
            ("azure.com", False),
            ("technet.microsoft.com", False),
            ("openai.com", False),
            ("mit.edu", False),
            ("cern.ch", False),
            ("gov.uk", False),
            ("defense-cyber.org", False),
            ("acme-corporation.net", False),
            ("threat-intel-feed.com", False),
        ]

        false_positives = 0
        false_negatives = 0

        for domain, expected_noise in dataset:
            detected_noise = is_noise_domain(domain)
            if detected_noise and not expected_noise:
                false_positives += 1
            elif not detected_noise and expected_noise:
                false_negatives += 1

        # Accuracy must be 100% on this benchmark
        assert false_positives == 0, f"False positive noise flags: {false_positives}"
        assert false_negatives == 0, f"False negative noise misses: {false_negatives}"

    def test_benchmark_deduplication_integrity(self):
        """Verifies duplicate occurrences across casing and URLs are deduplicated."""
        raw_urls = [
            "https://microsoft.com/en-us/about?utm_source=twitter&utm_medium=social",
            "https://MICROSOFT.COM/en-us/about",
            "https://microsoft.com/en-us/about/",
            "https://microsoft.com/en-us/about?ref=share",
        ]
        from recursive_osint.search.deduplication import canonicalize_url

        canonical_urls = {canonicalize_url(u) for u in raw_urls}
        assert len(canonical_urls) == 1, f"Expected 4 duplicate URLs to resolve to 1 canonical URL, got {len(canonical_urls)}"

    @pytest.mark.asyncio
    async def test_get_lead_graph_provenance_and_edge_semantics(self, db_session):
        """Verifies that InvestigationService.get_lead_graph builds edges with provenance and relationship_kind."""
        from recursive_osint.services.investigation_service import InvestigationService
        from recursive_osint.schemas.investigation import InvestigationCreate

        service = InvestigationService(db_session)
        inv = await service.create_investigation(
            user_id=None,
            data=InvestigationCreate(
                title="Test Provenance",
                target_clue="contoso.com",
                clue_type="domain",
            ),
        )
        graph = await service.get_lead_graph(inv.id)
        assert len(graph.nodes) >= 1
        for edge in graph.edges:
            assert edge.relationship_kind in ("direct", "inferred", "unverified")
            assert edge.confidence_rationale is not None
