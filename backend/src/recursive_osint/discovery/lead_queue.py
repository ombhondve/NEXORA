"""
Lead Priority Queue.
Prioritizes leads based on confidence, relevance, and depth.
"""

import heapq
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set


@dataclass(order=True)
class PrioritizedLeadItem:
    # Priority is inverted because heapq is a min-heap (lower value = popped first)
    priority: float
    depth: int
    lead_id: str = field(compare=False)
    lead_type: str = field(compare=False)
    lead_value: str = field(compare=False)
    discovery_reason: str = field(compare=False)


class LeadPriorityQueue:
    """Bounded, thread-safe in-memory priority queue for investigation leads."""

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self._heap: List[PrioritizedLeadItem] = []
        self._seen_values: Set[str] = set()

    def push(
        self,
        lead_id: str,
        lead_type: str,
        lead_value: str,
        depth: int,
        priority_score: float,
        discovery_reason: str = "",
    ) -> bool:
        normalized = lead_value.strip().lower()
        if normalized in self._seen_values:
            return False

        if len(self._heap) >= self.max_size:
            return False

        self._seen_values.add(normalized)
        # Invert priority so that high priority_score is popped first
        item = PrioritizedLeadItem(
            priority=-priority_score,
            depth=depth,
            lead_id=lead_id,
            lead_type=lead_type,
            lead_value=lead_value,
            discovery_reason=discovery_reason,
        )
        heapq.heappush(self._heap, item)
        return True

    def pop(self) -> Optional[PrioritizedLeadItem]:
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)
