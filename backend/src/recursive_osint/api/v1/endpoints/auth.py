"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.api.dependencies import get_current_user
from recursive_osint.db.session import get_db
from recursive_osint.db.models.user import User
from recursive_osint.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from recursive_osint.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new investigator account."""
    service = AuthService(db)
    return await service.register(user_in)


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates credentials and returns JWT bearer token."""
    service = AuthService(db)
    return await service.login(login_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieves profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
