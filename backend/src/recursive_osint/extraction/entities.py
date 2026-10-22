"""
Entity Extraction and Normalization.
Extracts public entities, domains, dates, organizations, and identifiers from retrieved text.
Includes strict noise filtering, domain categorization, and lead candidate eligibility.
"""

import re
from typing import List, Dict, Any, Set
from dataclasses import dataclass, field


# Domains representing video sharing, LMS, social networks, search engines, CDNs,
# and generic reference services that must NEVER be promoted as autonomous investigative leads.
NOISE_DOMAINS: Set[str] = {
    # Video & Media Platforms
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "dailymotion.com",
    "twitch.tv",
    # LMS & Educational Platforms
    "moodle.org",
    "instructure.com",
    "canvas.instructure.com",
    "blackboard.com",
    "edx.org",
    "coursera.org",
    "khanacademy.org",
    # Social Networks
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "linkedin.com",
    "reddit.com",
    "pinterest.com",
    # Reference, Knowledge & Archives
    "wikipedia.org",
    "wikimedia.org",
    "wikidata.org",
    "archive.org",
    "web.archive.org",
    # Developer Platforms & Package Registries
    "github.com",
    "github.io",
    "gitlab.com",
    "bitbucket.org",
    "sourceforge.net",
    "npmjs.com",
    "npm.im",
    "pypi.org",
    "crates.io",
    # Search Engines & Web Portals
    "google.com",
    "bing.com",
    "yahoo.com",
    "duckduckgo.com",
    "baidu.com",
    "yandex.com",
    # Infrastructure, CDN & Cloud Services
    "cloudflare.com",
    "fastly.net",
    "akamai.com",
    "amazonaws.com",
    "cloudfront.net",
    "azurewebsites.net",
    # Generic Standards, Examples & Academic Aggregators
    "example.com",
    "example.org",
    "example.net",
    "w3.org",
    "schema.org",
    "doi.org",
    "dx.doi.org",
    "ietf.org",
    "gnu.org",
    "apache.org",
    "creativecommons.org",
    "mozilla.org",
    # Blogging & CMS Platforms
    "wordpress.com",
    "wordpress.org",
    "medium.com",
    "blogspot.com",
    "blogger.com",
    "substack.com",
}


def is_noise_domain(domain: str) -> bool:
    """Checks whether a domain matches or is a subdomain of a known generic/noise domain."""
    if not domain:
        return True
    d_norm = domain.lower().strip().rstrip(".")
    # Direct match
    if d_norm in NOISE_DOMAINS:
        return True
    # Subdomain check (e.g. canvas.instructure.com -> instructure.com)
    for noise in NOISE_DOMAINS:
        if d_norm.endswith("." + noise):
            return True
    return False


@dataclass
class RawEntity:
    entity_type: str
    entity_value: str
    normalized_value: str
    confidence: float
    context_snippet: str
    is_lead_candidate: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class EntityExtractor:
    """Regex and pattern-based entity extraction with context preservation and noise filtering."""

    # Regex patterns
    DOMAIN_REGEX = re.compile(
        r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|io|ai|dev|co|uk|de|ch|fr|info|biz|me|tech)\b",
        re.IGNORECASE,
    )
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    DOI_REGEX = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
    DATE_REGEX = re.compile(
        r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? (?:19|20)\d{2}\b",
        re.IGNORECASE,
    )
    ORG_REGEX = re.compile(
        r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:Inc|Corp|LLC|Ltd|Foundation|University|Institute|Alliance|Labs|Group|Consortium|Association)\b"
    )

    # Generic / boilerplate words to exclude from extracted organizations
    GENERIC_ORG_EXCLUSIONS = {
        "terms of service inc",
        "privacy policy llc",
        "all rights reserved corp",
        "cookie policy inc",
        "read more corp",
    }

    @classmethod
    def extract_all(cls, text: str, target_clue: str = "") -> List[RawEntity]:
        entities: List[RawEntity] = []
        if not text:
            return entities

        seen = set()
        target_lower = target_clue.lower().strip() if target_clue else ""

        def add_entity(
            e_type: str,
            raw_val: str,
            norm_val: str,
            conf: float,
            start_idx: int,
            is_lead: bool = True,
            meta: Dict[str, Any] = None,
        ):
            key = (e_type, norm_val)
            if key not in seen:
                seen.add(key)
                snippet_start = max(0, start_idx - 50)
                snippet_end = min(len(text), start_idx + len(raw_val) + 50)
                snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()
                entities.append(
                    RawEntity(
                        entity_type=e_type,
                        entity_value=raw_val,
                        normalized_value=norm_val,
                        confidence=conf,
                        context_snippet=snippet,
                        is_lead_candidate=is_lead,
                        metadata=meta or {},
                    )
                )

        # 1. Domains (Filtered for common noise)
        for match in cls.DOMAIN_REGEX.finditer(text):
            val = match.group()
            norm = val.lower().rstrip(".")
            if norm.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".css", ".js")):
                continue

            # Check if domain is generic noise (YouTube, Canvas LMS, Moodle, etc.)
            if is_noise_domain(norm):
                # We can record as secondary reference, but NEVER promote as an investigative lead
                add_entity(
                    "domain",
                    val,
                    norm,
                    0.30,
                    match.start(),
                    is_lead=False,
                    meta={"category": "generic_third_party_service"},
                )
            else:
                # Assess relevance to target clue
                is_target_related = bool(target_lower and (target_lower in norm or norm in target_lower))
                conf = 0.85 if is_target_related else 0.70
                add_entity(
                    "domain",
                    val,
                    norm,
                    conf,
                    match.start(),
                    is_lead=True,
                    meta={"category": "target_infrastructure" if is_target_related else "discovered_domain"},
                )

        # 2. Emails (Public contact patterns)
        for match in cls.EMAIL_REGEX.finditer(text):
            val = match.group()
            norm = val.lower()
            # Filter generic email patterns
            if any(norm.startswith(prefix) for prefix in ("support@", "info@", "privacy@", "abuse@", "webmaster@", "admin@")):
                add_entity("email", val, norm, 0.40, match.start(), is_lead=False, meta={"generic": True})
            else:
                add_entity("email", val, norm, 0.80, match.start(), is_lead=True)

        # 3. DOIs / Academic identifiers
        for match in cls.DOI_REGEX.finditer(text):
            val = match.group()
            norm = val.lower()
            add_entity("identifier", val, norm, 0.90, match.start(), is_lead=True)

        # 4. Dates (Extracted as temporal metadata, NEVER as recursive search leads)
        for match in cls.DATE_REGEX.finditer(text):
            val = match.group()
            norm = val
            add_entity(
                "date",
                val,
                norm,
                0.60,
                match.start(),
                is_lead=False,  # DATES ARE TEMPORAL ATTRIBUTES, NEVER SEARCH LEADS
                meta={"temporal_attribute": True},
            )

        # 5. Organizations
        for match in cls.ORG_REGEX.finditer(text):
            val = match.group().strip()
            norm = val.lower()
            if norm not in cls.GENERIC_ORG_EXCLUSIONS and len(val.split()) <= 6:
                is_target_related = bool(target_lower and (target_lower in norm or norm in target_lower))
                conf = 0.85 if is_target_related else 0.75
                add_entity("organization", val, norm, conf, match.start(), is_lead=True)

        return entities
