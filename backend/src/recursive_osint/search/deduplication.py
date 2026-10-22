"""
URL Normalization and Content Deduplication.
"""

import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Set

# Tracking parameters that should be stripped for canonicalization
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "ncid", "zanpid"
}


def canonicalize_url(raw_url: str) -> str:
    """
    Normalizes a URL by lowercasing scheme/host, removing tracking parameters,
    sorting query parameters, and stripping fragments and trailing slashes.
    """
    try:
        parsed = urlparse(raw_url.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        # Strip standard tracking queries
        filtered_queries = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS
        ]
        filtered_queries.sort()
        query_str = urlencode(filtered_queries)

        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # No fragment
        return urlunparse((scheme, netloc, path, parsed.params, query_str, ""))
    except Exception:
        return raw_url.strip()


def compute_content_hash(text: str) -> str:
    """Computes SHA-256 hash of normalized text."""
    # Collapse whitespaces
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
