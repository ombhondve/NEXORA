"""
Query Planner and Expansion.
Intelligently generates targeted follow-up queries based on discovered clues and entities.
"""

from typing import List
from recursive_osint.schemas.search import SearchRequest


class QueryExpansionEngine:
    """Generates context-aware queries for multi-source OSINT discovery."""

    @staticmethod
    def expand_initial_clue(clue: str, clue_type: str = "text") -> List[str]:
        """Generates initial targeted queries based on clue type."""
        clue = clue.strip()
        queries = [clue]

        if clue_type == "domain":
            domain = clue.replace("http://", "").replace("https://", "").split("/")[0]
            queries.extend([
                f'"{domain}"',
                f'site:{domain}',
                f'"{domain}" security OR privacy OR contact',
                f'"{domain}" registration OR whois',
            ])
        elif clue_type == "name":
            queries.extend([
                f'"{clue}"',
                f'"{clue}" biography OR profile',
                f'"{clue}" organization OR company',
                f'"{clue}" research OR publications',
            ])
        elif clue_type == "url":
            queries.extend([
                f'"{clue}"',
                clue.split("?")[0],
            ])
        else:
            # Generic text clue
            queries.extend([
                f'"{clue}" overview',
                f'"{clue}" official report',
                f'"{clue}" organization',
            ])

        return queries[:4]

    @staticmethod
    def generate_followup_queries(entity_value: str, entity_type: str, parent_clue: str) -> List[str]:
        """Generates targeted follow-up queries correlating a discovered entity with the parent investigation clue."""
        queries: List[str] = []
        if entity_type == "domain":
            queries.append(f'"{parent_clue}" site:{entity_value}')
            queries.append(f'"{parent_clue}" "{entity_value}"')
        elif entity_type in ("organization", "person"):
            queries.append(f'"{parent_clue}" AND "{entity_value}"')
            queries.append(f'"{entity_value}" overview')
        elif entity_type == "email":
            domain = entity_value.split("@")[-1]
            queries.append(f'"{domain}"')
        else:
            queries.append(f'"{parent_clue}" "{entity_value}"')

        return queries[:2]
