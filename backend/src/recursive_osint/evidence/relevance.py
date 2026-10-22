"""
Evidence Relevance and Transparency Evaluator.
Computes calibrated heuristic relevance scores, uncertainty metrics, and transparent inclusion rationales.
Separates source reliability, topical focus, fact confidence, and simulated data markers.
"""

import re
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass


# Source reliability weights based on provenance integrity
SOURCE_RELIABILITY_WEIGHTS: Dict[str, float] = {
    "openalex": 0.90,           # Peer-reviewed academic registry
    "crossref": 0.90,           # Official scholarly DOI registry
    "wikidata": 0.85,           # Structured curated knowledge base
    "wikipedia": 0.80,          # Community-curated encyclopedia with citations
    "github_public": 0.70,      # Open-source public repositories
    "internet_archive": 0.65,   # Historical archival snapshots
    "searxng": 0.60,            # General metasearch engine aggregation
    "mock_demo": 0.15,          # Synthetic mock records (unverified)
}

# Substantive relational predicates indicating real organizational or infrastructure connection
RELATIONAL_PREDICATES = {
    "headquarters", "founded", "founder", "ceo", "president", "director", "executive",
    "subsidiary", "parent company", "acquired", "acquisition", "merged", "partnership",
    "developer", "developed by", "created by", "author", "maintainer", "infrastructure",
    "domain", "server", "ip address", "asn", "datacenter", "certificate", "whois",
    "corporation", "enterprise", "division", "patent", "trademark", "operations",
}

# Common incidental / passing phrases that do NOT represent direct organizational facts
INCIDENTAL_INDICATORS = {
    "works on", "runs on", "compatible with", "download for", "watch on", "listen on",
    "available on", "follow us on", "share on", "powered by", "cookie policy",
    "terms of use", "all rights reserved", "system requirements",
}


@dataclass
class EvidenceEvaluation:
    relevance_score: float
    uncertainty_score: float
    confidence_level: str
    why_included: str
    source_reliability: float
    is_incidental: bool


class EvidenceEvaluator:
    """Evaluates passage relevance and evidence uncertainty with calibrated heuristic rules."""

    @staticmethod
    def evaluate_passage(
        passage: str,
        clue: str,
        source_name: str,
        title: str = "",
        is_simulated: bool = False,
    ) -> Tuple[float, float, str, str]:
        """
        Evaluates a retrieved passage against the target clue with documented heuristic criteria.

        Returns:
            relevance_score (0.0 to 1.0)
            uncertainty_score (0.0 to 1.0)
            confidence_level ("high", "medium", "low", "unverified")
            why_included (Transparent heuristic explanation)
        """
        evaluation = EvidenceEvaluator.evaluate_detailed(
            passage=passage,
            clue=clue,
            source_name=source_name,
            title=title,
            is_simulated=is_simulated,
        )
        return (
            evaluation.relevance_score,
            evaluation.uncertainty_score,
            evaluation.confidence_level,
            evaluation.why_included,
        )

    @staticmethod
    def evaluate(
        clue: str,
        passage: str,
        source_name: str,
        title: str = "",
        is_simulated: bool = False,
    ) -> Tuple[float, str, str]:
        """Convenience method returning (relevance_score, confidence_level, why_included)."""
        evaluation = EvidenceEvaluator.evaluate_detailed(
            passage=passage,
            clue=clue,
            source_name=source_name,
            title=title,
            is_simulated=is_simulated,
        )
        return (
            evaluation.relevance_score,
            evaluation.confidence_level,
            evaluation.why_included,
        )

    @staticmethod
    def evaluate_detailed(
        passage: str,
        clue: str,
        source_name: str,
        title: str = "",
        is_simulated: bool = False,
    ) -> EvidenceEvaluation:
        # Case A: Simulated / Mock Connector Data
        if is_simulated or source_name.lower() in ("mock_demo", "mock"):
            return EvidenceEvaluation(
                relevance_score=0.15,
                uncertainty_score=0.85,
                confidence_level="unverified",
                why_included="[Simulated Source] Synthetic demo record generated for testing; excluded from verified findings.",
                source_reliability=0.15,
                is_incidental=True,
            )

        p_lower = passage.lower()
        t_lower = title.lower()
        c_lower = clue.lower().strip()

        # Source reliability lookup
        connector_key = source_name.lower().replace(" ", "_").replace("-", "_")
        source_rel = SOURCE_RELIABILITY_WEIGHTS.get(connector_key, 0.60)

        # Tokenize clue
        clue_tokens = [t for t in re.split(r"\W+", c_lower) if len(t) > 2]
        if not clue_tokens:
            clue_tokens = [c_lower]

        exact_in_title = c_lower in t_lower
        exact_in_passage = c_lower in p_lower
        matched_tokens = [t for t in clue_tokens if t in p_lower]
        match_ratio = len(matched_tokens) / len(clue_tokens) if clue_tokens else 0.0

        # Check for relational context predicates
        has_relational_predicate = any(pred in p_lower for pred in RELATIONAL_PREDICATES)

        # Check if the clue is only used in an incidental / boilerplate phrase
        is_incidental = any(phrase in p_lower for phrase in INCIDENTAL_INDICATORS) and not exact_in_title

        # Heuristic Scoring Logic:
        # 1. Central Topical Match: Target in title AND substantive context in passage
        if exact_in_title and (exact_in_passage or match_ratio >= 0.8):
            relevance = round(min(0.92, 0.78 + (0.14 * source_rel)), 2)
            uncertainty = 0.20
            confidence = "high"
            why = (
                f"Central topical focus: target clue '{clue}' features prominently in title "
                f"and body text of {source_name} (source reliability: {int(source_rel * 100)}%)."
            )

        # 2. Substantive Contextual Match: Target in passage with relational predicates
        elif exact_in_passage and has_relational_predicate and not is_incidental:
            relevance = round(min(0.78, 0.65 + (0.12 * source_rel)), 2)
            uncertainty = 0.35
            confidence = "medium"
            why = (
                f"Substantive contextual match: target clue '{clue}' appears with operational or "
                f"organizational predicates in {source_name}."
            )

        # 3. Incidental Match: Target string occurs in passing or in boilerplate/compatibility list
        elif exact_in_passage and is_incidental:
            relevance = 0.35
            uncertainty = 0.75
            confidence = "low"
            why = (
                f"Incidental mention: target string '{clue}' appears in a peripheral, platform, "
                f"or compatibility context in {source_name}. Requires independent corroboration."
            )

        # 4. Standard Exact Match without relational predicates
        elif exact_in_passage:
            relevance = round(min(0.65, 0.40 + (0.15 * source_rel)), 2)
            uncertainty = round(1.0 - (0.45 * source_rel), 2)
            confidence = "medium" if source_rel >= 0.80 else "low"
            why = (
                f"Direct keyword match for '{clue}' in {source_name} (source reliability: {int(source_rel * 100)}%); "
                f"context is descriptive but lacks explicit organizational predicates."
            )

        # 5. Token Match (Multi-word clue partial overlap)
        elif match_ratio >= 0.65:
            relevance = 0.45
            uncertainty = 0.60
            confidence = "low"
            why = (
                f"Partial token overlap ({len(matched_tokens)}/{len(clue_tokens)} terms) with '{clue}' "
                f"in {source_name}."
            )

        # 6. Weak / Exploratory Correlation
        else:
            relevance = 0.20
            uncertainty = 0.85
            confidence = "unverified"
            why = f"Exploratory result from {source_name}; contextual correlation to '{clue}' is unverified."

        return EvidenceEvaluation(
            relevance_score=relevance,
            uncertainty_score=uncertainty,
            confidence_level=confidence,
            why_included=why,
            source_reliability=source_rel,
            is_incidental=is_incidental,
        )
