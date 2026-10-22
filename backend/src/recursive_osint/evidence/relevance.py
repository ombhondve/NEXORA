"""
Evidence Relevance and Transparency Evaluator.
Computes objective relevance scores, uncertainty metrics, and inclusion rationale.
"""

import re
from typing import Tuple, Dict, Any


class EvidenceEvaluator:
    """Evaluates passage relevance and evidence uncertainty."""

    @staticmethod
    def evaluate_passage(
        passage: str,
        clue: str,
        source_name: str,
    ) -> Tuple[float, float, str, str]:
        """
        Returns:
            relevance_score (0.0 to 1.0)
            uncertainty_score (0.0 to 1.0)
            confidence_level ("high", "medium", "low", "unverified")
            why_included (Transparent explanation)
        """
        p_lower = passage.lower()
        c_lower = clue.lower().strip()

        # Tokenize clue
        clue_tokens = [t for t in re.split(r"\W+", c_lower) if len(t) > 2]
        if not clue_tokens:
            clue_tokens = [c_lower]

        exact_match = c_lower in p_lower
        matched_tokens = [t for t in clue_tokens if t in p_lower]
        match_ratio = len(matched_tokens) / len(clue_tokens) if clue_tokens else 0.0

        if exact_match:
            relevance = 0.90
            uncertainty = 0.15
            confidence = "high"
            why = (
                f"Contains exact verbatim match for target clue '{clue}' in verified "
                f"public source ({source_name})."
            )
        elif match_ratio >= 0.7:
            relevance = 0.75
            uncertainty = 0.35
            confidence = "medium"
            why = (
                f"Contains strong keyword correlation ({len(matched_tokens)}/{len(clue_tokens)} terms) "
                f"to clue '{clue}' in source {source_name}."
            )
        elif match_ratio > 0.0:
            relevance = 0.45
            uncertainty = 0.65
            confidence = "low"
            why = (
                f"Partial token overlap detected ({len(matched_tokens)}/{len(clue_tokens)} terms). "
                f"Requires human analyst corroboration before concluding connection."
            )
        else:
            relevance = 0.20
            uncertainty = 0.85
            confidence = "unverified"
            why = f"Discovered via exploratory link from {source_name}; contextual connection is unverified."

        return relevance, uncertainty, confidence, why
