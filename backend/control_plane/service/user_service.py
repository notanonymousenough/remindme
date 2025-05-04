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
        # TODO model dump in repo
        user = request.model_dump(exclude_unset=True)
        user_id = user.pop('id')
        return await self.repo.update_user(user_id=user_id, user=user)

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
        # TODO model dump in repo
        user = user.model_dump(exclude=telegram_data_only)

        if not (user_to_update := await self.get_user_by_telegram_id(user["telegram_id"])):  # If user doesn't exist
            return await self.repo.create_user(user)
        return await self.update_user_from_telegram_data(user_to_update)

    async def update_user_from_telegram_data(self, user_to_update: UserSchema) -> UserSchema:
        # TODO model dump in repo
        user = user_to_update.model_dump(exclude_unset=True)
        user_id = user.pop('id')
        return UserSchema.model_validate(await self.repo.update_user(user_id, user))


_user_service = UserService()


def get_user_service():
    return _user_service
