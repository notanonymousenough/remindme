from typing import Sequence
from uuid import UUID

from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest, HabitSchemaPutRequest, \
    HabitProgressSchemaPostRequest


class HabitService:
    def __init__(self):
        self.repo = HabitRepository()

    async def habits_get(self, user_id: UUID) -> Sequence[HabitSchemaResponse]:
        return await self.repo.habits_get(user_id=user_id)

    async def habits_post(self, user_id: UUID, request: HabitSchemaPostRequest) -> HabitSchemaResponse:
        return await self.repo.habits_post(user_id=user_id, request=request)

    async def habit_put(self, request: HabitSchemaPutRequest) -> HabitSchemaResponse:
        return await self.repo.habit_put(request=request)

    async def habit_delete(self, user_id: UUID, model_id: UUID) -> bool:
        return await self.repo.habit_delete(user_id=user_id, model_id=model_id)

    async def habit_get(self, model_id: UUID) -> HabitSchemaResponse:
        return await self.repo.habit_get(model_id=model_id)

    async def habit_put_name(self, request: HabitSchemaPutRequest) -> HabitSchemaResponse:
        return await self.repo.habit_put(request=request)

    # habit progress table
    async def habit_progress_post(self, request: HabitProgressSchemaPostRequest) -> HabitProgressSchemaPostRequest:
        return await self.repo.habit_progress_post(request=request)

    async def habit_progress_delete_last_record(self, habit_id: UUID) -> bool:
        return await self.repo.habit_progress_delete_last_record(habit_id=habit_id)


_habit_service = HabitService()


def get_habit_service():
    return _habit_service
