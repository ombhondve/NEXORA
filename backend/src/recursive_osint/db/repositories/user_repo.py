"""
User repository for authentication and profile management.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from recursive_osint.db.models.user import User
from recursive_osint.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.strip().lower())
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_api_key(self, api_key: str) -> Optional[User]:
        stmt = select(User).where(User.api_key == api_key)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
