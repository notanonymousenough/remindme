from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import update, and_

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models import User
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.schemas.user import UserTelegramDataSchema, UserSchema


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def get_user(self, user_id: UUID) -> UserSchema | None:
        response = await self.repo.get_user(user_id=user_id)
        return UserSchema.model_validate(response)

    async def get_user_by_telegram_id(self, telegram_id: str) -> UserSchema | None:
        user = await self.repo.get_user_by_telegram_id(telegram_id)
        if user is None:
            raise HTTPException(404, "User by telegram id not found")

        return UserSchema.model_validate(user)

    async def create_or_update_user_from_telegram_data(self, user: UserTelegramDataSchema) -> UserSchema:
        return await self.repo.create_or_update_user(user=user)


_user_service = UserService()


def get_user_service():
    return _user_service
