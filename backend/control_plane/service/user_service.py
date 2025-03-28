from uuid import UUID

from sqlalchemy import select, update

from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models import User
from backend.control_plane.db.repositories.user import UserRepository
from backend.control_plane.schemas.user import UserTelegramDataSchema


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def get_user_by_user_id(self, user_id: UUID) -> User | None:
        # return await self.repo.get(user_id)  # TODO(Arsen)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.repo.get_user_by_telegram_id(telegram_id)

    async def create_or_update_user(
            self,
            user_data: UserTelegramDataSchema,
    ) -> None:
        """
        User is created if doesn't exist based on telegram_id.
        If exists check whether there are modified values.
        Updates modified values.
        """
        async with await get_async_session() as session:
            user = _user_service.get_user_by_telegram_id(user_data.telegram_id)
            if user is None:
                session.add(User(**user_data.model_dump()))
                return
            db_values = user.__dict__
            if values_to_update := {
                key: value
                for key, value in user_data.model_dump().items()
                if db_values[key] != value
            }:
                await session.execute(
                    update(User)
                    .where(User.telegram_id == user_data.telegram_id)
                    .values(values_to_update)
                )


_user_service = UserService()


def get_user_service():
    return _user_service
