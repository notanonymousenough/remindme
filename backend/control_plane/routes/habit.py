from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.params import Body

from backend.control_plane.schemas.requests.habit import HabitSchemaPostRequest, HabitSchemaPutRequest, \
    HabitProgressSchemaPostRequest
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.habit_service import HabitService, get_habit_service
from backend.control_plane.utils.auth import get_authorized_user

habit_router = APIRouter(
    prefix="/habit",
    tags=["habit"]
)


@habit_router.get(
    path="/"
)
async def habits_get(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        user: UserSchema = Depends(get_authorized_user)
):
    return await habit_service.habits_get(user_id=user.id)


@habit_router.post(
    path="/"
)
async def habits_post(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        request: HabitSchemaPostRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
):
    return await habit_service.habits_post(user_id=user.id, request=request)


@habit_router.put(
    path="/{habit_id}"
)
async def habit_put(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        request: HabitSchemaPutRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
):
    return await habit_service.habit_put(request=request)


@habit_router.delete(
    path="/{habit_id}",
    responses={
        200: {
            "description": "Привычка удалена"
        }
    }
)
async def habit_delete(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        habit_id: UUID,
        user: UserSchema = Depends(get_authorized_user)
):
    return await habit_service.habit_delete(user_id=user.id, model_id=habit_id)


@habit_router.post(
    path="/{habit_id}/progress"
)
async def habit_progress_post(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        request: HabitProgressSchemaPostRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
):
    return await habit_service.habit_progress_post(request=request)

