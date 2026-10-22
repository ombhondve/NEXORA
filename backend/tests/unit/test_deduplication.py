"""
URL Canonicalization and Content Hashing Unit Tests.
"""

from recursive_osint.search.deduplication import canonicalize_url, compute_content_hash


def test_canonicalize_url_strips_tracking_params():
    raw_url = "https://EXAMPLE.org/articles/news?utm_source=twitter&utm_medium=social&id=102#header"
    expected = "https://example.org/articles/news?id=102"
    assert canonicalize_url(raw_url) == expected


def test_canonicalize_url_sorts_query_parameters():
    raw1 = "https://example.org/search?z=1&a=2&m=3"
    raw2 = "https://example.org/search?a=2&m=3&z=1"
    assert canonicalize_url(raw1) == canonicalize_url(raw2)


def test_canonicalize_url_removes_standard_ports():
    assert canonicalize_url("http://example.org:80/page") == "http://example.org/page"
    assert canonicalize_url("https://example.org:443/page") == "https://example.org/page"


def test_compute_content_hash_deterministic():
    text1 = "  Recursive  OSINT Discovery  Engine \n\t "
    text2 = "recursive osint discovery engine"
    assert compute_content_hash(text1) == compute_content_hash(text2)
