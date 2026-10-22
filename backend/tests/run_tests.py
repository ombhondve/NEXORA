"""
Hermetic Test Runner using Python Standard Library unittest.
Runs all unit and logic tests without external dependencies.
"""

import sys
import unittest
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recursive_osint.core.exceptions import SSRFViolationError, BudgetExhaustedError
from recursive_osint.core.security import validate_url_safe, hash_password, verify_password
from recursive_osint.search.deduplication import canonicalize_url, compute_content_hash
from recursive_osint.discovery.budget import InvestigationBudget
from recursive_osint.discovery.stopping_rules import StoppingRules
from recursive_osint.discovery.lead_queue import LeadPriorityQueue
from recursive_osint.extraction.entities import EntityExtractor
from recursive_osint.evidence.relevance import EvidenceEvaluator
from recursive_osint.connectors.mock_demo import MockDemoConnector
from recursive_osint.connectors.registry import connector_registry
import asyncio


class TestSSRFSecurity(unittest.TestCase):
    def test_ssrf_blocks_loopback(self):
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("http://127.0.0.1:8080/admin")
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("http://localhost:3000")

    def test_ssrf_blocks_rfc1918(self):
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("http://192.168.1.1/gateway")
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("http://10.0.0.5/api")

    def test_ssrf_blocks_cloud_metadata(self):
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("http://169.254.169.254/latest/meta-data/")

    def test_ssrf_blocks_bad_protocols(self):
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("file:///etc/passwd")
        with self.assertRaises(SSRFViolationError):
            validate_url_safe("gopher://127.0.0.1:70")

    def test_ssrf_permits_safe_url(self):
        url = "https://example.org/public"
        self.assertEqual(validate_url_safe(url), url)


class TestDeduplication(unittest.TestCase):
    def test_canonicalize_url(self):
        raw = "https://EXAMPLE.org/path/?utm_source=twitter&b=2&a=1#section"
        expected = "https://example.org/path?a=1&b=2"
        self.assertEqual(canonicalize_url(raw), expected)

    def test_content_hash_deterministic(self):
        t1 = "  Recursive   OSINT   Engine \n"
        t2 = "recursive osint engine"
        self.assertEqual(compute_content_hash(t1), compute_content_hash(t2))


class TestStoppingRulesAndBudget(unittest.TestCase):
    def test_budget_query_limit(self):
        budget = InvestigationBudget(max_total_queries=2)
        budget.record_query()
        budget.record_query()
        with self.assertRaises(BudgetExhaustedError):
            budget.record_query()

    def test_budget_bytes_limit(self):
        budget = InvestigationBudget(max_download_bytes=100)
        with self.assertRaises(BudgetExhaustedError):
            budget.record_bytes(150)

    def test_stopping_on_cancel(self):
        budget = InvestigationBudget()
        should_stop, reason = StoppingRules.evaluate(budget, 0, False, is_cancelled=True)
        self.assertTrue(should_stop)
        self.assertIn("cancelled", reason.lower())

    def test_lead_priority_queue(self):
        queue = LeadPriorityQueue()
        queue.push("1", "domain", "low-priority.org", 1, 0.3)
        queue.push("2", "domain", "high-priority.org", 1, 0.95)
        top = queue.pop()
        self.assertIsNotNone(top)
        self.assertEqual(top.lead_value, "high-priority.org")


class TestEntityExtractionAndRelevance(unittest.TestCase):
    def test_extraction(self):
        text = "Security team at sec@nexora.org identified rogue host portal.nexora.org on 2024-05-12."
        entities = EntityExtractor.extract_all(text)
        types = {e.entity_type for e in entities}
        self.assertIn("email", types)
        self.assertIn("domain", types)

    def test_relevance_evaluator(self):
        rel, uncert, conf, why = EvidenceEvaluator.evaluate_passage(
            "Verbatim match for NEXORA Operations confirmed.",
            "NEXORA Operations",
            "Mock Registry",
        )
        self.assertGreaterEqual(rel, 0.85)
        self.assertEqual(conf, "high")
        self.assertIn("exact", why.lower())


class TestMockConnector(unittest.TestCase):
    def test_mock_search(self):
        connector = MockDemoConnector()
        self.assertTrue(connector.is_configured)
        results = asyncio.run(connector.search("Sovereign Infrastructure", 2))
        self.assertGreater(len(results), 0)
        self.assertIn("Simulated", results[0].title)


if __name__ == "__main__":
    unittest.main(verbosity=2)
