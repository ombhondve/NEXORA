"""
Stopping Rules and Budget Enforcement Unit Tests.
"""

import pytest
from recursive_osint.core.exceptions import BudgetExhaustedError
from recursive_osint.discovery.budget import InvestigationBudget
from recursive_osint.discovery.stopping_rules import StoppingRules


def test_budget_enforces_max_queries():
    budget = InvestigationBudget(max_total_queries=3)
    budget.record_query()
    budget.record_query()
    budget.record_query()
    with pytest.raises(BudgetExhaustedError):
        budget.record_query()


def test_budget_enforces_max_downloads():
    budget = InvestigationBudget(max_download_bytes=1000)
    budget.record_bytes(500)
    with pytest.raises(BudgetExhaustedError):
        budget.record_bytes(600)


def test_stopping_rules_cancels_early():
    budget = InvestigationBudget(max_total_queries=20)
    should_stop, reason = StoppingRules.evaluate(
        budget=budget,
        consecutive_zero_results=0,
        lead_queue_empty=False,
        is_cancelled=True,
    )
    assert should_stop is True
    assert "cancelled" in reason.lower()


def test_stopping_rules_diminishing_returns():
    budget = InvestigationBudget(max_total_queries=20)
    should_stop, reason = StoppingRules.evaluate(
        budget=budget,
        consecutive_zero_results=5,
        lead_queue_empty=False,
        is_cancelled=False,
    )
    assert should_stop is True
    assert "diminishing returns" in reason.lower()
