from uuid import UUID

from fastapi import HTTPException

from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.schemas.user import UserTelegramDataSchema, UserSchema


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def get_user(self, user_id: UUID) -> UserSchema | None:
        response = await self.repo.get_by_model_id(user_id)
        return UserSchema.model_validate(response)

    async def update_user(self, request: UserSchema) -> UserSchema:
        return await self.repo.update_user(user=request)

    async def get_user_by_telegram_id(self, telegram_id: str) -> UserSchema | None:
        user = await self.repo.get_user_by_telegram_id(telegram_id)
        if user is None:
            raise HTTPException(404, "User by telegram id not found")
        return UserSchema.model_validate(user)

    async def create_user_from_telegram_data(self, user: UserTelegramDataSchema) -> UserSchema:
        """
        User is created if doesn't exist based on telegram_id.
        If exists check whether there are modified values.
        Updates modified values.
        """
        telegram_data_only = {"photo_url", "auth_date", "hash"}
        user = user.model_dump(exclude=telegram_data_only)

        if not (user_to_update := await self.get_user_by_telegram_id(user["telegram_id"])):  # If user doesn't exist
            return await self.repo.create_user(UserSchema.model_validate(user))
        return await self.update_user_from_telegram_data(user_to_update)

    async def update_user_from_telegram_data(self, user_to_update: UserSchema) -> UserSchema:
        return UserSchema.model_validate(await self.repo.update_user(UserSchema.model_validate(user_to_update)))


_user_service = UserService()


def get_user_service():
    return _user_service
