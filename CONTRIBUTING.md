# Contributing to Recursive OSINT Discovery Engine

We welcome contributions adhering to high software engineering and security standards.

## Development Workflow
1. Fork and clone the repository.
2. Copy `.env.example` to `.env` and configure local development variables.
3. Install backend dependencies: `pip install -e ".[dev]"`
4. Install frontend dependencies: `npm install`
5. Run tests: `pytest backend/tests`
6. Run linter: `ruff check backend/src`

## Code Standards
- **Strict Typing**: All backend code must use modern type annotations (Python 3.11+). All frontend code must pass TypeScript strict checks.
- **Security First**: Every new connector or crawler must inherit from `BaseSourceConnector` and utilize SSRF-protected HTTP clients.
- **Deterministic Tests**: Tests must not rely on live internet connections or paid third-party APIs. Mock fixtures and simulated responses must be provided.
- **Documentation**: All public endpoints and core services require descriptive docstrings.
