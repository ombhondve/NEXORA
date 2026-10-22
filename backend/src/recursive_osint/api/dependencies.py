"""
FastAPI route dependencies.
"""

from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.core.exceptions import SecurityException
from recursive_osint.core.security import decode_access_token
from recursive_osint.db.session import get_db
from recursive_osint.db.models.user import User
from recursive_osint.db.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extracts and validates current authenticated user from JWT token."""
    if not auth:
        # For development / test convenience or demo, allow a default investigator
        repo = UserRepository(db)
        user = await repo.get_by_email("demo@example.org")
        if not user:
            from recursive_osint.core.security import hash_password
            user = User(
                email="demo@example.org",
                hashed_password=hash_password("password123"),
                full_name="OSINT Analyst",
                role="investigator",
            )
            user = await repo.create(user)
            await db.commit()
        return user

    try:
        payload = decode_access_token(auth.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
        
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
        return user
    except SecurityException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
