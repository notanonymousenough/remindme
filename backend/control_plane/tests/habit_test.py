import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.db.models import HabitPeriod
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitPostRequest


@pytest.mark.usefixtures("TestHabit")
class TestHabitAPI:
    @pytest.mark.asyncio
    async def test_habit_post(self,
                              session: AsyncSession,
                              auth_user: dict,
                              client: httpx.AsyncClient):
        habit_request = {
            "text": "habitTest0",
            "interval": HabitPeriod.WEEKLY
        }
        habit = HabitPostRequest.model_validate(habit_request)
        response = await client.post("/v1/habit/", headers=auth_user, data=habit.model_dump_json())

        habit = HabitSchemaResponse.model_validate(response.json())
        assert habit.text == habit_request["text"]
        # TODO ассерты остальных ручек