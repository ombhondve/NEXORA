"""
Budget tracking and limits for recursive investigations.
"""

import time
from typing import Optional
from recursive_osint.core.exceptions import BudgetExhaustedError


class InvestigationBudget:
    """Tracks and enforces resource consumption per investigation."""

    def __init__(
        self,
        max_depth: int = 3,
        max_total_queries: int = 25,
        max_execution_seconds: int = 600,
        max_download_bytes: int = 52428800,  # 50 MB
        max_ai_tokens: int = 25000,
    ):
        self.max_depth = max_depth
        self.max_total_queries = max_total_queries
        self.max_execution_seconds = max_execution_seconds
        self.max_download_bytes = max_download_bytes
        self.max_ai_tokens = max_ai_tokens

        # Counters
        self.queries_executed = 0
        self.bytes_downloaded = 0
        self.tokens_used = 0
        self.start_time = time.time()

    def record_query(self) -> None:
        self.queries_executed += 1
        if self.queries_executed > self.max_total_queries:
            raise BudgetExhaustedError(
                f"Maximum query budget of {self.max_total_queries} queries exceeded."
            )

    def record_bytes(self, byte_count: int) -> None:
        self.bytes_downloaded += byte_count
        if self.bytes_downloaded > self.max_download_bytes:
            raise BudgetExhaustedError(
                f"Maximum download budget of {self.max_download_bytes} bytes exceeded."
            )

    def record_tokens(self, token_count: int) -> None:
        self.tokens_used += token_count
        if self.tokens_used > self.max_ai_tokens:
            raise BudgetExhaustedError(
                f"Maximum AI token budget of {self.max_ai_tokens} tokens exceeded."
            )

    def check_time(self) -> None:
        elapsed = time.time() - self.start_time
        if elapsed > self.max_execution_seconds:
            raise BudgetExhaustedError(
                f"Maximum execution time of {self.max_execution_seconds}s exceeded."
            )

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def is_depth_allowed(self, depth: int) -> bool:
        return depth <= self.max_depth
