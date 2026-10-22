"""
Stopping rules evaluation for recursive investigations.
"""

from typing import Tuple
from recursive_osint.discovery.budget import InvestigationBudget


class StoppingRules:
    """Evaluates whether an investigation should terminate."""

    @staticmethod
    def evaluate(
        budget: InvestigationBudget,
        consecutive_zero_results: int,
        lead_queue_empty: bool,
        is_cancelled: bool,
    ) -> Tuple[bool, str]:
        """
        Returns (should_stop, reason)
        """
        if is_cancelled:
            return True, "Investigation cancelled by user."

        try:
            budget.check_time()
        except Exception as e:
            return True, str(e)

        if budget.queries_executed >= budget.max_total_queries:
            return True, f"Total query budget of {budget.max_total_queries} queries reached."

        if lead_queue_empty:
            return True, "No further relevant leads remaining in priority queue."

        if consecutive_zero_results >= 5:
            return True, "Diminishing returns: 5 consecutive queries returned no new information."

        return False, ""
