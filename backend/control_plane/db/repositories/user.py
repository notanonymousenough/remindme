from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..engine import get_async_session
from ..models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user_by_telegram_id(self, telegram_id) -> User | None:
        async with await get_async_session() as session:
            state = select(self.model).where(getattr(self.model, telegram_id) == telegram_id)
            user = await session.execute(state)
            return user.scalars().one_or_none()