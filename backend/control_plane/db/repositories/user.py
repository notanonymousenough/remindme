from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.future import select

from ..engine import get_async_session
from ..models.user import User
from .base import BaseRepository
from ...schemas.user import UserTelegramDataSchema, UserSchema


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user(self, user_id: UUID) -> UserSchema | None:
        async with await get_async_session() as session:
            result = await session.get(User, user_id)
            if result is None:
                return None
            return UserSchema.model_validate(result)

    async def get_user_by_telegram_id(self, telegram_id: str) -> UserSchema | None:
        async with await get_async_session() as session:
            state = select(self.model).where(
                and_(
                    getattr(self.model, "telegram_id") == telegram_id
                )
            )
            result = (await session.execute(state)).scalars().one_or_none()
            return UserSchema.model_validate(result) if result else None

    async def create_user(self, user: UserSchema) -> UserSchema:
        async with await get_async_session() as session:
            obj = User(**user.model_dump())  # convert user to db model(obj)
            session.add(obj)
            await session.commit()
            return UserSchema.model_validate(obj)  # convert db model(obj) to user

    async def update_user(self, user: UserSchema) -> UserSchema:
        async with await get_async_session() as session:
            if not (db_user := await session.get(User, user.id)):
                raise HTTPException(404, "User not found")

            for key, value in user.model_dump(exclude_unset=True).items():
                setattr(db_user, key, value)

            await session.commit()
            await session.refresh(db_user)
            return UserSchema.model_validate(db_user)

    async def create_or_update_user_from_telegram_data(self, user: UserTelegramDataSchema) -> UserSchema:
        """
        User is created if doesn't exist based on telegram_id.
        If exists check whether there are modified values.
        Updates modified values.
        """
        telegram_data_only = {"photo_url", "auth_date", "hash"}
        user = user.model_dump(exclude=telegram_data_only)

        if not (user_to_update := await self.get_user_by_telegram_id(user["telegram_id"])):  # If user doesn't exist
            return await self.create_user(UserSchema.model_validate(user))

        return UserSchema.model_validate(await self.update_user(UserSchema.model_validate(user_to_update)))
