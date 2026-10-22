"""
FastAPI route dependencies with strict production authorization.
"""

from typing import AsyncGenerator
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


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extracts and validates current authenticated user from JWT token."""
    if not auth:
        if settings.ENVIRONMENT != "production" and settings.ALLOW_ANONYMOUS_DEV_AUTH:
            # Only allowed if explicitly toggled on in development mode
            repo = UserRepository(db)
            user = await repo.get_by_email("demo@example.org")
            if user and user.is_active:
                return user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or are invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(auth.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except SecurityException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
