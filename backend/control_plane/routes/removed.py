from typing import Annotated, Sequence

from cfgv import remove_defaults
from fastapi import APIRouter, Body
from fastapi.params import Depends
from fastapi import FastAPI, Query, HTTPException, Response, status
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.removed import RemovedEntitiesIDs, RemovedEntities
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.remover_service import RemovedService, get_removed_service
from backend.control_plane.utils.auth import get_authorized_user

removed_router = APIRouter(
    prefix="/removed",
    tags=["Removed"],
)


@removed_router.get("/")
async def removed_habits_reminders(
        removed_service: Annotated[RemovedService, Depends(get_removed_service)],
        user: Annotated[UserSchema, Depends(get_authorized_user)]
) -> RemovedEntities:
    return await removed_service.get_removed_reminders_habits(user_id=user.id)


@removed_router.post("/")
async def restore_removed_habits_reminders(
        removed_service: Annotated[RemovedService, Depends(get_removed_service)],
        user: Annotated[UserSchema, Depends(get_authorized_user)],
        request: RemovedEntitiesIDs = Body(...)
) -> None:
    return await removed_service.restore_removed(request.reminder_id, request.habit_id)
