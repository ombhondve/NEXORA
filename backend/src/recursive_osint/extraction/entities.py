"""
Entity Extraction and Normalization.
Extracts public entities, domains, dates, organizations, and identifiers from retrieved text.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class RawEntity:
    entity_type: str
    entity_value: str
    normalized_value: str
    confidence: float
    context_snippet: str


class EntityExtractor:
    """Regex and pattern-based entity extraction with context preservation."""

    # Regex patterns
    DOMAIN_REGEX = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|edu|gov|io|ai|dev|co|uk|de|ch|fr)\b", re.IGNORECASE)
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    DOI_REGEX = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
    DATE_REGEX = re.compile(r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? (?:19|20)\d{2}\b", re.IGNORECASE)
    ORG_REGEX = re.compile(r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:Inc|Corp|LLC|Ltd|Foundation|University|Institute|Alliance|Labs|Group|Consortium|Association)\b")

    @classmethod
    def extract_all(cls, text: str) -> List[RawEntity]:
        entities: List[RawEntity] = []
        if not text:
            return entities

        seen = set()

        def add_entity(e_type: str, raw_val: str, norm_val: str, conf: float, start_idx: int):
            key = (e_type, norm_val)
            if key not in seen:
                seen.add(key)
                # Extract surrounding snippet (+/- 40 chars)
                snippet_start = max(0, start_idx - 40)
                snippet_end = min(len(text), start_idx + len(raw_val) + 40)
                snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()
                entities.append(
                    RawEntity(
                        entity_type=e_type,
                        entity_value=raw_val,
                        normalized_value=norm_val,
                        confidence=conf,
                        context_snippet=snippet,
                    )
                )

        # Domains
        for match in cls.DOMAIN_REGEX.finditer(text):
            val = match.group()
            norm = val.lower()
            if not norm.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf")):
                add_entity("domain", val, norm, 0.85, match.start())

        # Emails (Public contact patterns)
        for match in cls.EMAIL_REGEX.finditer(text):
            val = match.group()
            norm = val.lower()
            add_entity("email", val, norm, 0.80, match.start())

        # DOIs / Academic identifiers
        for match in cls.DOI_REGEX.finditer(text):
            val = match.group()
            norm = val.lower()
            add_entity("identifier", val, norm, 0.95, match.start())

        # Dates
        for match in cls.DATE_REGEX.finditer(text):
            val = match.group()
            norm = val
            add_entity("date", val, norm, 0.75, match.start())

        # Organizations
        for match in cls.ORG_REGEX.finditer(text):
            val = match.group().strip()
            norm = val.lower()
            add_entity("organization", val, norm, 0.80, match.start())

        return entities
