# Troubleshooting Guide

### 1. SSRF Violation Error (HTTP 403)
**Symptom**: Outbound crawler requests fail with `SSRF_VIOLATION`.
**Remedy**: The engine strictly prohibits private IP spaces (RFC1918), loopback (`127.0.0.1`), link-local (`169.254.0.0/16`), and non-standard ports. Ensure target URLs are publicly routed hostnames over port 80 or 443.

### 2. Rate Limit Exceeded (HTTP 429)
**Symptom**: `RATE_LIMIT_EXCEEDED` error returned on API queries.
**Remedy**: Sliding window rate limits apply per client IP and connector. Wait for the retry-after window or adjust `DEFAULT_MAX_REQUESTS_PER_CONNECTOR` in `.env`.

### 3. Investigation Halts with "Diminishing Returns"
**Symptom**: Investigation status marked `completed` before reaching max depth.
**Remedy**: If five consecutive search queries return no new entities or URLs, the stopping rules trigger to prevent wasted budget. Try supplying a more specific or differentiated search clue.
