from .base import BaseRepository
from ..models.achievement import AchievementTemplate, UserAchievement


class AchievementTemplateRepository(BaseRepository[AchievementTemplate]):
    def __init__(self):
        super().__init__(AchievementTemplate)


class UserAchievementRepository(BaseRepository[UserAchievement]):
    def __init__(self):
        super().__init__(UserAchievement)
