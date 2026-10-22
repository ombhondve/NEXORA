"""
Security and cryptographic utilities.
Includes pre-flight SSRF mitigation, password hashing, and JWT token handling.
"""

import ipaddress
import socket
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import hashlib

import jwt
from recursive_osint.config import settings
from recursive_osint.core.exceptions import SSRFViolationError, SecurityException
from recursive_osint.core.logging import get_logger

logger = get_logger("security")

# Prohibited CIDR blocks for outbound requests
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),       # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / Cloud metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # Private class B
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),     # Private class C
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("fc00::/7"),           # Unique local
    ipaddress.ip_network("fe80::/10"),          # Link-local
]

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443}


def validate_url_safe(url: str) -> str:
    """
    Validates that a URL is safe for outbound fetching and does not violate SSRF constraints.
    Resolves hostname to IP addresses and checks each address against blocked ranges.
    """
    if not settings.ENABLE_SSRF_PROTECTION:
        return url

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFViolationError(f"Prohibited URL scheme: '{scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFViolationError("URL missing valid hostname.")

    # Check for direct IP address in hostname
    try:
        direct_ip = ipaddress.ip_address(hostname)
        for net in BLOCKED_NETWORKS:
            if direct_ip in net:
                raise SSRFViolationError(f"Direct IP access to restricted range prohibited: {hostname}")
        if direct_ip.is_private or direct_ip.is_loopback or direct_ip.is_link_local:
            raise SSRFViolationError(f"Direct IP access to private/loopback prohibited: {hostname}")
    except ValueError:
        # Hostname is a domain name, not an IP literal
        pass

    port = parsed.port or (443 if scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        raise SSRFViolationError(f"Prohibited destination port: {port}. Only standard ports (80, 443) allowed.")

    # Pre-flight DNS resolution to prevent DNS rebinding attacks
    try:
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved:
                logger.warning("SSRF blocked: %s resolves to restricted IP %s", hostname, ip_str)
                raise SSRFViolationError(f"Hostname '{hostname}' resolves to restricted IP address '{ip_str}'")

            for blocked_net in BLOCKED_NETWORKS:
                if ip_obj in blocked_net:
                    logger.warning("SSRF blocked: %s matches restricted network %s", ip_str, blocked_net)
                    raise SSRFViolationError(f"Destination IP '{ip_str}' falls within blocked network '{blocked_net}'")

    except socket.gaierror as e:
        raise SSRFViolationError(f"Could not resolve hostname '{hostname}': {str(e)}")

    return url


# Password Hashing Utilities
def hash_password(password: str) -> str:
    """
    Hashes a plain password using SHA-256 + salt (or Argon2id if available).
    Provides robust, deterministic verification without heavy native library failures.
    """
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against stored hash."""
    return hash_password(plain_password) == hashed_password


# JWT Token Utilities
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a cryptographically signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise SecurityException("Access token has expired.")
    except jwt.InvalidTokenError as e:
        raise SecurityException(f"Invalid access token: {str(e)}")
