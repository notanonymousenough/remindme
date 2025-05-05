from typing import Sequence
from uuid import UUID

from backend.control_plane.db.repositories.habit import HabitRepository
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest, HabitSchemaPutRequest, \
    HabitProgressSchemaPostRequest


class HabitService:
    def __init__(self):
        self.repo = HabitRepository()

    async def find_habits_by_user_id(self, user_id: UUID) -> Sequence[HabitSchemaResponse]:
        return await self.repo.find_habits_by_user_id(user_id=user_id)

    async def create_habit(self, user_id: UUID, request: HabitSchemaPostRequest) -> HabitSchemaResponse:
        return await self.repo.create_habit(user_id=user_id, request=request.model_dump())

    async def habit_update(self, request: HabitSchemaPutRequest) -> HabitSchemaResponse:
        request = request.model_dump()
        model_id = request.pop("habit_id")
        response = await self.repo.update_model(model_id=model_id, **request)
        return HabitSchemaResponse.model_validate(response)

    async def remove_habit(self, user_id: UUID, model_id: UUID) -> bool:
        return await self.repo.delete_model(user_id=user_id, model_id=model_id)

    async def habit_get(self, model_id: UUID) -> HabitSchemaResponse:
        response = await self.repo.get_by_model_id(model_id=model_id)
        return HabitSchemaResponse.model_validate(response)

    # habit progress table
    async def add_habit_progress(self, request: HabitProgressSchemaPostRequest) -> HabitProgressSchemaPostRequest:
        return await self.repo.add_habit_progress(request=request.model_dump())

    async def habit_progress_delete_last_record(self, habit_id: UUID) -> bool:
        return await self.repo.habit_progress_delete_last_record(habit_id=habit_id)


_habit_service = HabitService()


def get_habit_service():
    return _habit_service
