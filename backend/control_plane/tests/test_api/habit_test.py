import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.habit_tools import get_last_record_status_bool
from backend.control_plane.db.models import HabitPeriod, Habit
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitPostRequest, HabitPutRequest
from backend.control_plane.schemas.requests.habit_progress import HabitProgressRequest


@pytest.mark.usefixtures("TestHabit")
class TestHabitAPI:
    @pytest.mark.asyncio
    async def test_habit_post(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient
    ):
        habit_request = {
            "text": "habitTest0",
            "interval": HabitPeriod.WEEKLY
        }
        habit = HabitPostRequest.model_validate(habit_request)
        response = await client.post("/v1/habit/", headers=auth_user, data=habit.model_dump_json())

        response_data = HabitSchemaResponse.model_validate(response.json())
        assert response_data.text == habit_request["text"]
        assert response_data.interval == HabitPeriod.WEEKLY

        async with await session as session:
            habit_from_db = await session.get(Habit, response_data.id)
        assert HabitSchemaResponse.model_validate(habit_from_db)

    @pytest.mark.asyncio
    async def test_habit_get(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient
    ):
        response = await client.get("/v1/habit/", headers=auth_user)
        assert response.status_code == 200

        habits = [HabitSchemaResponse.model_validate(response_model) for response_model in response.json()]
        assert habits

    @pytest.mark.asyncio
    async def test_habit_put(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient,
            TestHabit: HabitSchemaResponse
    ):
        habit_to_put = HabitPutRequest.model_validate(
            {
                "habit_id": TestHabit.id,
                "text": "Новый текст для TestHabit :)",
            }
        )
        response = await client.put(f"/v1/habit/{habit_to_put.habit_id}", data=habit_to_put.model_dump_json(),
                                    headers=auth_user)
        assert response.status_code == 200

        new_habit_response = HabitSchemaResponse.model_validate(response.json())
        assert new_habit_response.id == habit_to_put.habit_id
        assert new_habit_response.text == habit_to_put.text

        async with await session as session:
            model_from_db = await session.get(Habit, habit_to_put.habit_id)
        assert HabitSchemaResponse.model_validate(model_from_db)
        assert HabitSchemaResponse.model_validate(model_from_db).id == TestHabit.id

    @pytest.mark.asyncio
    async def test_habit_progress_post(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient,
            TestHabit: HabitSchemaResponse
    ):
        request = HabitProgressRequest.model_validate(
            {
                "habit_id": TestHabit.id
            }
        )

        response = await client.post(
            f"/v1/habit/{TestHabit.id}/progress",
            headers=auth_user,
            data=request.model_dump_json()
        )
        assert response.status_code == 200

        async with await session as session:
            updated_model_habit = await session.get(Habit, TestHabit.id)
            updated_habit = HabitSchemaResponse.model_validate(updated_model_habit)
        assert updated_habit
        assert get_last_record_status_bool(updated_habit) is True

    @pytest.mark.asyncio
    async def test_habit_delete(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient,
            TestHabit: HabitSchemaResponse
    ):
        response = await client.delete(
            f"/v1/habit/{TestHabit.id}",
            headers=auth_user
        )
        assert response.status_code == 200

        async with await session as session:
            habit_model_from_db = await session.get(Habit, TestHabit.id)
        removed_habit = HabitSchemaResponse.model_validate(habit_model_from_db)
        assert removed_habit
        assert removed_habit.removed is True