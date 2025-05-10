from typing import Annotated, Sequence

from fastapi import APIRouter
from fastapi import Depends

from backend.control_plane.schemas.achievementschema import AchievementSchema
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.achievement_service import get_achievement_service, AchievementService
from backend.control_plane.utils.auth import get_authorized_user

achievement_router = APIRouter(
    prefix="/achievement",
    tags=["Achievement"],
)


@achievement_router.get(
    path="/",
    response_model=None,
    responses={
        200: {
            "description": "Ачивки получены!"
        }
    }
)
async def user_achievements_get(
        achievement_service: Annotated[AchievementService, Depends(get_achievement_service)],
        user: UserSchema = Depends(get_authorized_user)
) -> Sequence[AchievementSchema]:
    return await achievement_service.get_unlocked_achievement(user.id)
