from typing import Sequence
from uuid import UUID

from backend.control_plane.db.repositories.achievement import UserAchievementRepository
from backend.control_plane.schemas.achievementschema import AchievementSchema


class AchievementService:
    def __init__(self):
        self.repo = UserAchievementRepository()

    async def get_unlocked_achievement(self, user_id: UUID) -> Sequence[AchievementSchema]:
        response = await self.repo.get_models(user_id=user_id)  # **{"progress": 100}
        return [AchievementSchema.model_validate(achievement_response) for achievement_response in response]


_achievement_service = AchievementService()


def get_achievement_service():
    return _achievement_service
