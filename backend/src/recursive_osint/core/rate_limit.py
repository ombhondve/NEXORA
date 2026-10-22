"""
In-memory and Redis-backed rate limiting using sliding window token buckets.
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from recursive_osint.core.exceptions import RateLimitExceededError


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter per key (e.g. IP, User UUID, or Connector)."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        """Checks if key is within rate limit; raises exception if exceeded."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean older requests outside the window
        timestamps = [t for t in self._history[key] if t > window_start]
        self._history[key] = timestamps

        if len(timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
            raise RateLimitExceededError(
                f"Rate limit exceeded for '{key}'. Try again in {retry_after} seconds.",
                details={"retry_after_seconds": retry_after},
            )

        self._history[key].append(now)
        return True


# Global rate limiter instances
api_rate_limiter = SlidingWindowRateLimiter(max_requests=120, window_seconds=60)
search_rate_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)
