from typing import Sequence
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..engine import get_async_session
from ..models.habit import Habit, HabitProgress
from ...schemas.habit import HabitSchemaResponse
from ...schemas.requests.habit import HabitSchemaPostRequest, HabitSchemaPutRequest, HabitProgressSchemaPostRequest


class HabitRepository(BaseRepository[Habit]):
    def __init__(self):
        super().__init__(Habit)

    async def habits_get(self, user_id: UUID) -> Sequence[HabitSchemaResponse]:
        async with await get_async_session() as session:
            stmt = select(self.model).where(
                and_(
                    getattr(self.model, "user_id") == user_id
                )
            ).options(selectinload(self.model.progress_records)) # Добавляем eager load
            result = await session.execute(stmt)
            response = result.scalars().all()
        return [HabitSchemaResponse.model_validate(obj) for obj in response]

    async def habits_post(self, user_id: UUID, request: HabitSchemaPostRequest) -> HabitSchemaResponse:
        async with await get_async_session() as session:
            obj = self.model(**vars(request))
            obj.user_id = user_id
            session.add(obj)
            await session.flush()
            await session.commit()
            await session.refresh(obj, attribute_names=['progress_records'])
            response = obj
        return HabitSchemaResponse.model_validate(response)

    async def habit_put(self, request: HabitSchemaPutRequest) -> HabitSchemaResponse:
        request_dict = request.model_dump()
        model_id = request_dict.pop("habit_id")
        response = await self.update_model(model_id=model_id, **vars(request_dict))
        return HabitSchemaResponse.model_validate(response)

    async def habit_delete(self, user_id: UUID, model_id: UUID) -> bool:
        return await self.delete_model(user_id=user_id, model_id=model_id)

    async def habit_get(self, model_id: UUID) -> HabitSchemaResponse:
        response = await self.get_by_model_id(model_id=model_id)
        return HabitSchemaResponse.model_validate(response)

    # habit_progress table
    async def habit_progress_post(self, request: HabitProgressSchemaPostRequest) -> HabitProgressSchemaPostRequest:
        async with await get_async_session() as session:
            obj = HabitProgress(**vars(request))
            session.add(obj)

            await session.flush()
            await session.commit()
            return HabitProgressSchemaPostRequest.model_validate(obj)
