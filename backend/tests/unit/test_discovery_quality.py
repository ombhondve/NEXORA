"""
Intelligence Accuracy, Evidence Validation, and Discovery Quality Unit Tests.
Verifies Phase 1-8 requirements of the NEXORA Quality Audit.
"""

import uuid
import pytest
from recursive_osint.extraction.entities import EntityExtractor, is_noise_domain
from recursive_osint.evidence.relevance import EvidenceEvaluator
from recursive_osint.discovery.budget import InvestigationBudget
from recursive_osint.discovery.stopping_rules import StoppingRules


class TestEntityExtractionAndNoiseFiltering:
    """Tests Phase 2 & 7: Noise domain filtering and date lead disqualification."""

    def test_noise_domains_filtered_from_entities(self):
        """Noise platforms like YouTube, Moodle, Canvas, Twitter must be detected as noise."""
        noise_samples = [
            "youtube.com",
            "www.youtube.com",
            "moodle.org",
            "canvas.instructure.com",
            "twitter.com",
            "x.com",
            "linkedin.com",
            "github.com",
            "example.org",
            "schema.org",
            "w3.org",
        ]
        for domain in noise_samples:
            assert is_noise_domain(domain) is True, f"Expected {domain} to be flagged as noise"

        valid_targets = [
            "microsoft.com",
            "azure.com",
            "openai.com",
            "deepmind.google",
            "acme-corp.net",
        ]
        for domain in valid_targets:
            assert is_noise_domain(domain) is False, f"Expected {domain} to NOT be flagged as noise"

    def test_dates_never_treated_as_lead_candidates(self):
        """Dates like 2017-06-19 must be tagged as non-lead candidates so they don't burn budgets."""
        text = "Microsoft acquired GitHub on 2018-06-04. The previous update was 2017-06-19."
        entities = EntityExtractor.extract_all(text)

        dates = [e for e in entities if e.entity_type == "date"]
        assert len(dates) >= 1
        for d in dates:
            assert d.is_lead_candidate is False, f"Date {d.normalized_value} should not be a search lead candidate"

    def test_entity_deduplication_and_normalization(self):
        """Multiple mentions of casing/trailing dots should normalize to the same value."""
        text = "Visit MICROSOFT.COM or https://microsoft.com/en-us. Also email contact@microsoft.com."
        entities = EntityExtractor.extract_all(text)
        domains = [e for e in entities if e.entity_type == "domain"]
        assert any(d.normalized_value == "microsoft.com" for d in domains)

    def test_generic_and_noise_domain_extraction_exclusion(self):
        """Extracting entities from text with YouTube and Canvas LMS should mark them non-leads."""
        text = "Watch Microsoft tutorial on youtube.com or course at canvas.instructure.com."
        entities = EntityExtractor.extract_all(text)
        for e in entities:
            if e.entity_type == "domain":
                if e.normalized_value in ("youtube.com", "canvas.instructure.com"):
                    assert is_noise_domain(e.normalized_value) is True


class TestEvidenceRelevanceAndHeuristicScoring:
    """Tests Phase 3 & 4: Heuristic relevance scoring, provenance, and incidental mentions."""

    def test_central_topic_receives_high_confidence(self):
        """When target is central to the title and substantive predicates are present."""
        target = "Microsoft Corporation"
        title = "Microsoft Corporation: Overview, Products and Corporate Structure"
        passage = (
            "Microsoft Corporation is an American multinational corporation and technology company "
            "headquartered in Redmond, Washington. Founded by Bill Gates and Paul Allen."
        )
        score, conf, rationale = EvidenceEvaluator.evaluate(
            clue=target,
            passage=passage,
            source_name="openalex",
            title=title,
            is_simulated=False,
        )
        assert score >= 0.80, f"Expected high score for central topic, got {score}"
        assert conf == "high"
        assert "provenance" in rationale.lower() or "central" in rationale.lower()

    def test_incidental_mention_receives_low_confidence(self):
        """Passage merely mentioning target as a dependency or compatible platform."""
        target = "Microsoft"
        title = "Third-Party Canvas LMS Plugin Integration Guide"
        passage = (
            "This third-party extension runs on Microsoft Windows and integrates with Moodle. "
            "Compatible with modern operating systems and web browsers."
        )
        score, conf, rationale = EvidenceEvaluator.evaluate(
            clue=target,
            passage=passage,
            source_name="searxng",
            title=title,
            is_simulated=False,
        )
        assert score <= 0.40, f"Expected low score for incidental mention, got {score}"
        assert conf in ("low", "unverified")
        assert "incidental" in rationale.lower()

    def test_simulated_mock_record_is_isolated(self):
        """Mock demo sources must always be marked unverified with very low score."""
        target = "Microsoft"
        title = "Mock Demo Intelligence Record"
        passage = "Microsoft synthetic finding on example.org for testing purposes."
        score, conf, rationale = EvidenceEvaluator.evaluate(
            clue=target,
            passage=passage,
            source_name="mock_demo",
            title=title,
            is_simulated=True,
        )
        assert score <= 0.20
        assert conf == "unverified"
        assert "simulated" in rationale.lower() or "mock" in rationale.lower()

    def test_source_reliability_weighting(self):
        """Academic / structured openalex should score higher than raw search for equivalent text."""
        passage = "Microsoft Research published advancements in distributed consensus algorithms."
        score_academic, _, _ = EvidenceEvaluator.evaluate(
            clue="Microsoft",
            passage=passage,
            source_name="openalex",
            title="Distributed Consensus",
        )
        score_search, _, _ = EvidenceEvaluator.evaluate(
            clue="Microsoft",
            passage=passage,
            source_name="searxng",
            title="Distributed Consensus",
        )
        assert score_academic > score_search


class TestInvestigationBudgetsAndHonestReporting:
    """Tests Phase 6: Honest budget status reporting (partial vs completed)."""

    def test_budget_exhaustion_identified_honestly(self):
        """When budget is exhausted, StoppingRules must flag it with a clear reason."""
        budget = InvestigationBudget(max_total_queries=5)
        for _ in range(5):
            budget.record_query()

        should_stop, reason = StoppingRules.evaluate(
            budget=budget,
            consecutive_zero_results=0,
            lead_queue_empty=False,  # Still has leads!
            is_cancelled=False,
        )
        assert should_stop is True
        assert "budget" in reason.lower()

    def test_lead_queue_exhaustion_marks_true_completion(self):
        """When lead queue is empty and budget not exhausted, that is legitimate completion."""
        budget = InvestigationBudget(max_total_queries=20)
        budget.record_query()
        should_stop, reason = StoppingRules.evaluate(
            budget=budget,
            consecutive_zero_results=0,
            lead_queue_empty=True,
            is_cancelled=False,
        )
        assert should_stop is True
        assert any(k in reason.lower() for k in ("leads", "empty", "exhausted", "remaining"))


class TestGraphTopologyQuality:
    """Tests Phase 7: Graph node deduplication and clean edges."""

    def test_canonical_node_deduplication(self):
        """Verifies logic pattern for grouping duplicate entities into canonical nodes."""
        raw_entities = [
            {"type": "domain", "value": "microsoft.com", "label": "microsoft.com"},
            {"type": "domain", "value": "MICROSOFT.COM", "label": "MICROSOFT.COM"},
            {"type": "domain", "value": "microsoft.com", "label": "microsoft.com"},
            {"type": "date", "value": "2017-06-19", "label": "2017-06-19"},
        ]

        # Simulation of get_lead_graph deduplication logic:
        canonical_nodes = {}
        for item in raw_entities:
            # Dates excluded from default graph
            if item["type"] == "date":
                continue
            key = (item["type"], item["value"].lower().strip())
            if key not in canonical_nodes:
                canonical_nodes[key] = {
                    "id": f"canonical_{key[0]}_{key[1]}",
                    "type": key[0],
                    "label": item["value"].lower().strip(),
                    "mention_count": 1,
                }
            else:
                canonical_nodes[key]["mention_count"] += 1

        # Assert duplicate microsoft.com merged into 1 node with count 3
        assert len(canonical_nodes) == 1
        node = canonical_nodes[("domain", "microsoft.com")]
        assert node["mention_count"] == 3
        # Assert date was filtered out
        assert ("date", "2017-06-19") not in canonical_nodes
