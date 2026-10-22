"""
FastAPI route dependencies with strict production authorization.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.config import settings
from recursive_osint.core.exceptions import SecurityException
from recursive_osint.core.security import decode_access_token
from recursive_osint.db.session import get_db
from recursive_osint.db.models.user import User
from recursive_osint.db.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_optional_user(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Extracts current authenticated user if Bearer token is provided and valid, otherwise returns None."""
    if not auth or not auth.credentials:
        return None

    try:
        payload = decode_access_token(auth.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None

        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Validates current authenticated user from JWT token.
    When REQUIRE_AUTH=false (default), authentication is optional and unauthenticated requests return None without error.
    When REQUIRE_AUTH=true, authentication is strictly enforced and missing credentials raise HTTP 401.
    """
    user = await get_optional_user(auth=auth, db=db)
    if user:
        return user

    if settings.REQUIRE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or are invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In public mode (REQUIRE_AUTH=False), return None without error
    return None

