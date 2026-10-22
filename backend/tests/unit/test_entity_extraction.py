"""
Entity Extraction Unit Tests.
"""

from recursive_osint.extraction.entities import EntityExtractor


def test_entity_extractor_finds_domains_emails_and_orgs():
    sample_text = (
        "Contact security officer at admin@nexora-defense.org regarding domain "
        "portal.nexora-defense.org. Affiliated with CyberSecurity Consortium."
    )
    entities = EntityExtractor.extract_all(sample_text)

    types = {e.entity_type for e in entities}
    assert "email" in types
    assert "domain" in types

    emails = [e for e in entities if e.entity_type == "email"]
    assert emails[0].normalized_value == "admin@nexora-defense.org"

    domains = [e for e in entities if e.entity_type == "domain"]
    assert any("nexora-defense.org" in d.normalized_value for d in domains)
