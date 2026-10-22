"""
SSRF Protection Unit Tests.
Verifies rejection of loopback, private RFC1918, link-local, cloud metadata, and invalid schemes.
"""

import pytest
from recursive_osint.core.exceptions import SSRFViolationError
from recursive_osint.core.security import validate_url_safe


def test_ssrf_blocks_loopback_ip():
    with pytest.raises(SSRFViolationError):
        validate_url_safe("http://127.0.0.1:8080/admin")

    with pytest.raises(SSRFViolationError):
        validate_url_safe("http://localhost:3000")


def test_ssrf_blocks_private_rfc1918_ips():
    with pytest.raises(SSRFViolationError):
        validate_url_safe("http://192.168.1.1/router")

    with pytest.raises(SSRFViolationError):
        validate_url_safe("http://10.0.0.5/internal")

    with pytest.raises(SSRFViolationError):
        validate_url_safe("http://172.16.0.10:80")


def test_ssrf_blocks_aws_cloud_metadata():
    with pytest.raises(SSRFViolationError):
        validate_url_safe("http://169.254.169.254/latest/meta-data/")


def test_ssrf_blocks_prohibited_protocols():
    with pytest.raises(SSRFViolationError):
        validate_url_safe("file:///etc/passwd")

    with pytest.raises(SSRFViolationError):
        validate_url_safe("gopher://127.0.0.1:70")

    with pytest.raises(SSRFViolationError):
        validate_url_safe("ftp://example.com/file")


def test_ssrf_blocks_non_standard_ports():
    with pytest.raises(SSRFViolationError):
        validate_url_safe("https://example.org:22")

    with pytest.raises(SSRFViolationError):
        validate_url_safe("https://example.org:3306")


def test_ssrf_permits_safe_public_url():
    # Valid public domain over https/port 443
    url = "https://example.org/public"
    validated = validate_url_safe(url)
    assert validated == url
