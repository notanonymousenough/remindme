from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.future import select

from ..engine import get_async_session
from ..models.user import User
from .base import BaseRepository
from ...schemas.user import UserSchema


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user_by_telegram_id(self, telegram_id: str) -> UserSchema | None:
        async with get_async_session() as session:
            state = select(self.model).where(
                and_(
                    getattr(self.model, "telegram_id") == telegram_id
                )
            )
            result = (await session.execute(state)).scalars().one_or_none()
            return UserSchema.model_validate(result) if result else None

    async def create_user(self, user: dict) -> UserSchema:
        async with get_async_session() as session:
            obj = User(**user)  # convert user to db model(obj)
            session.add(obj)
            await session.commit()
            return UserSchema.model_validate(obj)  # convert db model(obj) to user

    async def update_user(self, user_id: UUID, user: dict) -> UserSchema:
        async with get_async_session() as session:
            if not (db_user := await session.get(User, user_id)):
                raise HTTPException(404, "User not found")

            for key, value in user.items():
                setattr(db_user, key, value)

            await session.commit()
            await session.refresh(db_user)
            return UserSchema.model_validate(db_user)
