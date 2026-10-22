# Security Policy & Defensive Architecture

## 1. Ethical & Legal Boundaries
The **Recursive OSINT Discovery Engine** is designed strictly for lawful, authorized open-source intelligence research, cybersecurity defensive reconnaissance, academic research, and public interest investigations.

- **No Unauthorized Access**: The engine strictly queries public, authorized APIs and webpages. It does not bypass paywalls, authentication portals, CAPTCHAs, or platform security mechanisms.
- **Robots.txt & Rate Limits**: Automated crawlers obey `robots.txt` directives by default and adhere to respectful request delays and exponential backoff.
- **Privacy & Purpose Limitation**: The engine does not perform covert surveillance, unrestricted facial recognition across private individuals, or bulk harvesting of sensitive personal data. Uncertain identities are explicitly flagged with confidence scores.

## 2. Server-Side Request Forgery (SSRF) Mitigations
Network requests initiated by the ingestion engine and source connectors are passed through strict SSRF validation (`core/security.py`):
1. **IP Range Blacklisting**: Pre-flight resolution checks block RFC1918 private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), and AWS/GCP cloud metadata services (`169.254.169.254`).
2. **DNS Rebinding Protection**: DNS addresses are resolved immediately prior to socket connection, and redirect targets are independently re-checked.
3. **Protocol Whitelisting**: Only `http://` and `https://` schemes with standard ports (80, 443) are accepted.
4. **Payload & Timeout Limits**: Maximum response sizes (default 5 MB per webpage) and strict timeouts (15s) prevent slow-read and memory-exhaustion attacks.

## 3. Untrusted Data & Prompt Injection Defenses
All web content, retrieved documents, and external search snippets are classified as **untrusted data**:
- Content is parsed within isolated sandboxes.
- When AI models analyze text, user instructions are strictly segregated from document context. Documents are treated purely as passive data and cannot override system prompts or grant permissions.
- AI outputs are forced through rigid Pydantic schemas. Tool execution requires server-side validation.

## 4. File Upload Protection
- Uploaded files are verified via magic byte signatures (not merely filename extensions or user-controlled MIME headers).
- Randomized UUID filenames prevent path traversal.
- Uploaded files are stored outside of publicly served directories and served only through authenticated streaming endpoints.

## 5. Vulnerability Reporting
To report a security vulnerability, please contact `security@example.org` with details and reproduction steps.
