from uuid import UUID

import jwt
from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.future import select

from ..engine import get_async_session
from ..models.user import User
from .base import BaseRepository
from ...config import get_settings


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user(self, user_id: UUID) -> User | None:
        async with await get_async_session() as session:
            state = select(self.model).where(
                and_(
                    getattr(self.model, "id") == user_id
                )
            )

            result = await session.execute(state)
            await session.flush()
            return result.scalars().one()

    async def get_user_by_telegram_id(self, telegram_id: str) -> User | None:
        async with await get_async_session() as session:
            state = select(self.model).where(
                and_(
                    getattr(self.model, "telegram_id") == telegram_id
                )
            )

            result = await session.execute(state)
            await session.flush()
            return result.scalars().one_or_none()