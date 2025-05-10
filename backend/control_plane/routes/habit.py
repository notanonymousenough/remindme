from typing import Annotated, Sequence
from uuid import UUID

from aiohttp.web_response import Response
from fastapi import APIRouter, Depends
from fastapi.params import Body

from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitPostRequest, HabitPutRequest
from backend.control_plane.schemas.requests.habit_progress import HabitProgressRequest
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
) -> Sequence[HabitSchemaResponse]:
    return await habit_service.find_habits_by_user_id(user_id=user.id)


@habit_router.post(
    path="/"
)
async def habits_post(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        request: HabitPostRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
) -> HabitSchemaResponse:
    return await habit_service.create_habit(user_id=user.id, request=request)


@habit_router.put(
    path="/{habit_id}"
)
async def habit_put(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        request: HabitPutRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
) -> HabitSchemaResponse:
    return await habit_service.habit_update(request=request)


@habit_router.delete(
    path="/{habit_id}",
    responses={
        200: {
            "description": "Привычка удалена"
        },
        404: {
            "description": "Привычка не удалена"
        }
    },
    response_model=None
)
async def habit_delete(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        habit_id: UUID,
        user: UserSchema = Depends(get_authorized_user)
) -> Response:
    if await habit_service.remove_habit(model_id=habit_id):
        return Response(status=200, text="Привычка удалена")
    return Response(status=404)


@habit_router.post(
    path="/{habit_id}/progress"
)
async def habit_progress_post(
        habit_service: Annotated[HabitService, Depends(get_habit_service)],
        request: HabitProgressRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
):
    # TODO types
    return await habit_service.add_habit_progress(request=request)
