from uuid import UUID

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
        response = await self.repo.get_user_by_telegram_id(telegram_id)
        if response == None:
            return
        return UserSchema.model_validate(response)

    async def create_or_update_user(self, user_data: UserTelegramDataSchema) -> UserSchema:
        """
        User is created if doesn't exist based on telegram_id.
        If exists check whether there are modified values.
        Updates modified values.
        """
        async with await get_async_session() as session:  # TODO(Arsen) вынести в репо юзер
            user = await _user_service.get_user_by_telegram_id(user_data.telegram_id)
            if user is None:
                user_data = {key:value for key, value in user_data.model_dump().items()
                             if key not in ["photo_url", "auth_date", "hash"]}
                session.add(User(**user_data))
                await session.flush()
                await session.commit()

                return UserSchema.model_validate(user_data)

            db_values = user.__dict__
            if values_to_update := {
                key: value
                for key, value in user_data.model_dump().items()
                if not key in ["photo_url", "auth_date", "hash"]
                and db_values[key] != value
            }:
                stmt = update(User).where(
                    and_(
                        User.telegram_id == user_data.telegram_id
                    )
                ).values(values_to_update)
                result = await session.execute(stmt)
                user = result.scalars().one()
                return UserSchema.model_validate(user)
            return user


_user_service = UserService()


def get_user_service():
    return _user_service
