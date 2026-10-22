# Recursive OSINT Discovery Engine

A modular, secure, high-performance open-source intelligence (OSINT) discovery and correlation platform.

The engine begins with a user-provided search clue (text, domain, entity, or document) and autonomously discovers, extracts, deduplicates, and correlates findings across authorized, publicly accessible data sources through controlled recursive iterations.

---

## Key Features

- **Autonomous Recursive Discovery**: Controlled breadth/depth lead expansion with strict budget limits (max depth, query count, time, download bytes, and token caps).
- **Pluggable Source Connector Framework**:
  - **Free & Public Data Sources**: Internet Archive Wayback CDX API, Common Crawl Index, Wikipedia/Wikidata Open Knowledge APIs, CrossRef Open Scholarly Metadata, Open Corporates, and Public Web Search.
  - **Commercial Provider Support**: Optional adapters for Tavily, Brave Search, and Serper.
  - **Deterministic Mock Connector**: Fully functional simulated sources for hermetic local testing and offline demonstrations.
- **Enterprise Security & Defensive Design**:
  - **Pre-flight SSRF Guard**: Strict RFC1918, link-local, loopback, and cloud metadata blocking with DNS-rebinding protection.
  - **Robots.txt & Courtesy Engine**: Automated crawler delay, concurrency limits, and header identification.
  - **Prompt Injection Isolation**: External documents are framed strictly as untrusted data; schema enforcement via Pydantic v2.
  - **Cryptographic File Validation**: Magic byte signature checks, randomized storage IDs, and private uploads directory.
- **Evidence Provenance & Correlation**:
  - Automatic entity extraction (persons, organizations, domains, emails, locations, dates).
  - Explicit confidence scoring and identity uncertainty indicators.
  - Timeline generation and graph-structured parent-child lineage.
- **High-Performance Architecture**:
  - Asynchronous FastAPI backend with SQLAlchemy 2.0 (PostgreSQL + SQLite test fallback).
  - OpenSearch full-text and vector indexing.
  - Real-time investigation tracking via Server-Sent Events (SSE).
  - Modern Next.js 15 App Router frontend with dark cyber-investigation theme.

---

## Monorepo Architecture

```
recursive-osint/
├── apps/
│   └── web/                 # Next.js 15 App Router Frontend
├── backend/
│   ├── src/recursive_osint/ # FastAPI Core, Discovery Engine & Connectors
│   ├── migrations/          # Alembic DB Migrations
│   └── tests/               # Hermetic Pytest Suite
├── packages/
│   ├── shared-types/        # TypeScript interfaces matching backend models
│   ├── api-contracts/       # OpenAPI specifications and schema contracts
│   └── config/              # Central configuration schemas
├── infrastructure/          # Docker Compose, OpenSearch & Prometheus configs
├── scripts/                 # Development, migration, and seed scripts
└── docs/                    # Architecture, Data Flow, Security, and API docs
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- (Optional) Docker & Docker Compose for PostgreSQL, Redis, and OpenSearch

### 2. Environment Setup
Create dedicated environment files for frontend and backend:

**PowerShell (Windows):**
```powershell
Copy-Item apps/web/.env.example apps/web/.env.local
Copy-Item backend/.env.example backend/.env
```

**Bash (Linux / macOS):**
```bash
cp apps/web/.env.example apps/web/.env.local
cp backend/.env.example backend/.env
```

See [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) for full configuration options, production readiness, and Vercel deployment guides.

### 3. Backend Setup
```bash
python -m pip install -e ".[dev]"
python scripts/setup-dev.py
```

Run tests to verify the installation:
```bash
pytest backend/tests -v
```

Start the API server:
```bash
uvicorn recursive_osint.main:app --app-dir backend/src --reload --port 8000
```
Open interactive Swagger API documentation at: `http://localhost:8000/docs`

### 4. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```
Open the investigation dashboard at: `http://localhost:3000`

---

## Defensive Guardrails & Compliance
This software adheres to strict lawful reconnaissance standards. It contains no exploit capabilities, paywall/credential bypasses, or covert biometric tracking. See [SECURITY.md](SECURITY.md) for full details.
