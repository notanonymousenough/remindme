from uuid import UUID

from backend.control_plane.db.repositories.achievement import UserAchievementRepository


class AchievementService:
    def __init__(self):
        self.repo = UserAchievementRepository()

    async def get_unlocked_achievement(self, user_id: UUID):
        return await self.repo.get_models(user_id=user_id)


_achievement_service = AchievementService()


def get_achievement_service():
    return _achievement_service
