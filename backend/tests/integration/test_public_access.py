"""
Public Access & Unauthenticated Workflow Tests.
Verifies that all ordinary user endpoints (Live Search, Investigations, Reports, Sources)
function seamlessly without login, registration, or JWT tokens, while preserving
rate limits and input validation.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from recursive_osint.db.session import get_db
from recursive_osint.main import app
from recursive_osint.schemas.search import SearchResponse


@pytest.mark.asyncio
async def test_public_search_without_auth(db_session: AsyncSession):
    """Confirm POST /api/v1/search executes successfully with NO Authorization header."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post(
            "/api/v1/search",
            json={"query": "Cybersecurity Intelligence", "max_results": 5},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "Cybersecurity Intelligence"
        assert "results" in data
        assert isinstance(data["results"], list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_search_validation_errors(db_session: AsyncSession):
    """Confirm input validation on search is preserved (empty query rejected)."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Query too short (1 char < min_length 2)
        res_short = await client.post("/api/v1/search", json={"query": "x"})
        assert res_short.status_code == 422

        # 2. Query exceeding max length
        res_long = await client.post("/api/v1/search", json={"query": "a" * 501})
        assert res_long.status_code == 422

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_investigations_lifecycle_without_auth(db_session: AsyncSession):
    """
    Confirm full investigation lifecycle works without login or user token:
    1. Create investigation -> 201 Created (user_id is None)
    2. List investigations -> 200 OK
    3. Get investigation detail -> 200 OK
    4. Get investigation events -> 200 OK
    5. Get investigation report -> 200 OK
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Create without token
        create_res = await client.post(
            "/api/v1/investigations",
            json={
                "title": "Public Threat Actor OSINT",
                "target_clue": "APT-29 Cyber Threat",
                "clue_type": "text",
                "max_depth": 2,
                "max_total_queries": 10,
            },
        )
        assert create_res.status_code == 201
        inv_data = create_res.json()
        inv_id = inv_data["id"]
        assert inv_data["user_id"] is None
        assert inv_data["title"] == "Public Threat Actor OSINT"

        # 2. List without token
        list_res = await client.get("/api/v1/investigations")
        assert list_res.status_code == 200
        items = list_res.json()
        assert any(item["id"] == inv_id for item in items)

        # 3. Get detail without token
        detail_res = await client.get(f"/api/v1/investigations/{inv_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == inv_id

        # 4. Get events without token
        events_res = await client.get(f"/api/v1/investigations/{inv_id}/events")
        assert events_res.status_code == 200
        events = events_res.json()
        assert len(events) >= 1
        assert events[0]["event_type"] == "investigation_created"

        # 5. Get report without token
        report_res = await client.get(f"/api/v1/investigations/{inv_id}/report")
        assert report_res.status_code == 200
        report = report_res.json()
        assert report["investigation_id"] == inv_id

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_sources_without_auth(db_session: AsyncSession):
    """Confirm GET /api/v1/sources returns active connectors without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/api/v1/sources")
        assert res.status_code == 200
        sources = res.json()
        assert isinstance(sources, list)
        assert len(sources) >= 1


@pytest.mark.asyncio
async def test_auth_me_returns_public_analyst_without_token():
    """Confirm GET /api/v1/auth/me returns guest profile without failing with 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["full_name"] == "Public Analyst"
        assert data["is_active"] is True
