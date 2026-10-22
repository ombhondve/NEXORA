"""
Authentication Service.
Handles user registration, authentication, and JWT issuance.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from recursive_osint.core.exceptions import SecurityException, ValidationError
from recursive_osint.core.security import hash_password, verify_password, create_access_token
from recursive_osint.db.models.user import User
from recursive_osint.db.repositories.user_repo import UserRepository
from recursive_osint.schemas.auth import UserCreate, UserLogin, Token, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, user_in: UserCreate) -> UserResponse:
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise ValidationError(f"User with email '{user_in.email}' already exists.")

        user = User(
            email=user_in.email.strip().lower(),
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role or "investigator",
            is_active=True,
        )
        created = await self.user_repo.create(user)
        return UserResponse.model_validate(created)

    async def login(self, login_data: UserLogin) -> Token:
        user = await self.user_repo.get_by_email(login_data.email)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise SecurityException("Invalid email or password.")

        if not user.is_active:
            raise SecurityException("User account is inactive.")

        token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
        return Token(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
