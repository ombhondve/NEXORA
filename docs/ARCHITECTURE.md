# Architecture & System Design

## 1. Architectural Overview
The **Recursive OSINT Discovery Engine** is built as a modular monorepo combining:
- **FastAPI Core**: Asynchronous REST API managing investigations, users, queries, and reports.
- **Autonomous Recursive Engine**: Bounded priority-queue controller that iteratively expands leads, evaluates stopping rules, extracts entities, and cross-references sources.
- **Source Connector Framework**: Pluggable adapters querying Wikipedia, Internet Archive, CrossRef scholarly records, open corporate datasets, and external search APIs.
- **Defensive Security Layer**: Pre-flight SSRF protection, strict robots.txt compliance, URL canonicalization, and SHA-256 deduplication.
- **Next.js 15 Web Client**: App Router dashboard featuring real-time investigation progress, live timeline events, interactive evidence cards, and markdown report synthesis.

```mermaid
graph TD
    User([Investigator / Analyst]) -->|HTTPS / Next.js| WebApp[Next.js 15 Web Client]
    WebApp -->|REST API v1| FastAPI[FastAPI Backend Server]
    
    FastAPI --> Security[Pre-flight SSRF Guard & Auth]
    FastAPI --> DB[(PostgreSQL / SQLite)]
    FastAPI --> Redis[(Redis Cache & Task Queue)]
    FastAPI --> OpenSearch[(OpenSearch Index)]
    
    FastAPI --> Engine[Recursive Discovery Engine]
    Engine --> LeadQueue[Lead Priority Queue]
    Engine --> Budget[Investigation Budget Manager]
    Engine --> Connectors[Pluggable Connector Registry]
    
    Connectors --> Wiki[Wikipedia Open API]
    Connectors --> Archive[Internet Archive Wayback CDX]
    Connectors --> OpenData[CrossRef / Scholarly Open Data]
    Connectors --> Mock[Mock Demo Connector]
    
    Connectors --> Ingestion[Deduplication & Extraction]
    Ingestion --> Evidence[Relevance & Uncertainty Evaluator]
    Evidence --> DB
```

## 2. Key Modules
- **`backend/src/recursive_osint/discovery/`**: Contains the state machine, budget limits, lead priority queue, stopping rules, and recursive controller.
- **`backend/src/recursive_osint/connectors/`**: Base connector interface and implementations for public data sources.
- **`backend/src/recursive_osint/core/security.py`**: Strict SSRF guard, Argon2id/SHA-256 password hashing, and JWT handling.
- **`apps/web/`**: Next.js 15 frontend with dark cyber aesthetic, glassmorphic UI, and live status polling.
