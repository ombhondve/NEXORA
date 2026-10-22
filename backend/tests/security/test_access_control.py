"""
Cross-User Access Control & Authorization Security Tests.
Verifies that User B cannot access, read, start, cancel, or export User A's investigations.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from recursive_osint.core.security import hash_password, create_access_token
from recursive_osint.db.models.user import User
from recursive_osint.main import app


@pytest.mark.asyncio
async def test_cross_user_isolation(client: AsyncClient, db_session: AsyncSession, test_user: User):
    # 1. User A creates an investigation
    create_payload = {
        "title": "User A Classified Dossier",
        "target_clue": "Classified Clue A",
        "clue_type": "text",
        "max_depth": 2,
    }
    create_res = await client.post("/api/v1/investigations", json=create_payload)
    assert create_res.status_code == 201
    inv_id = create_res.json()["id"]

    # 2. Create User B (unauthorized third-party)
    user_b = User(
        email="unauthorized_b@example.org",
        hashed_password=hash_password("Pass123456!"),
        full_name="User B",
        role="investigator",
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    token_b = create_access_token({"sub": user_b.id, "email": user_b.email, "role": user_b.role})

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {token_b}"},
    ) as client_b:
        # Attempt to read User A's investigation
        get_res = await client_b.get(f"/api/v1/investigations/{inv_id}")
        assert get_res.status_code == 403
        assert get_res.json()["error"] == "ACCESS_DENIED"

        # Attempt to read User A's evidence
        ev_res = await client_b.get(f"/api/v1/investigations/{inv_id}/evidence")
        assert ev_res.status_code == 403

        # Attempt to cancel User A's investigation
        cancel_res = await client_b.post(f"/api/v1/investigations/{inv_id}/cancel")
        assert cancel_res.status_code == 403

        # Attempt to generate report on User A's investigation
        report_res = await client_b.get(f"/api/v1/investigations/{inv_id}/report")
        assert report_res.status_code == 403
