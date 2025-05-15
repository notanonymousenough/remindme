import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.control_plane.schemas.achievementschema import AchievementSchema


class TestAchievementAPI:
    @pytest.mark.asyncio
    async def test_achievement_get(
            self,
            session: AsyncSession,
            auth_user: dict,
            client: httpx.AsyncClient,
            TestAchievement: AchievementSchema
    ):
        assert TestAchievement
        response = await client.get("/v1/achievement/", headers=auth_user)
        assert response.status_code == 200
        achievements = [AchievementSchema.model_validate(response_model) for response_model in response.json()]
        assert achievements
        assert achievements[0].progress == TestAchievement.progress
