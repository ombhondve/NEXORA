# API Contracts & OpenAPI Specifications

This directory contains versioned API contract specifications matching the FastAPI OpenAPI schema.

## Endpoints Summary
- `POST /api/v1/investigations`: Create new recursive investigation
- `GET /api/v1/investigations`: List investigations
- `GET /api/v1/investigations/{id}`: Get investigation details
- `POST /api/v1/investigations/{id}/start`: Start autonomous discovery run
- `POST /api/v1/investigations/{id}/cancel`: Cancel active investigation
- `GET /api/v1/investigations/{id}/events`: Chronological audit and discovery events
- `GET /api/v1/investigations/{id}/evidence`: Correlated evidence records
- `GET /api/v1/investigations/{id}/report`: Synthesized executive report
- `POST /api/v1/search`: On-demand multi-source search
- `GET /api/v1/sources`: Source connector statuses and coverage info
- `GET /api/v1/health/live`: Liveness check
- `GET /api/v1/health/ready`: Readiness check
