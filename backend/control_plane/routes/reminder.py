from typing import Annotated, Sequence

from aiohttp.web_response import Response
from fastapi import APIRouter, Depends

from backend.control_plane.config import get_settings
from backend.control_plane.schemas.requests.reminder import ReminderMarkAsCompleteRequestSchema
from backend.control_plane.service.reminder_service import get_reminder_service, RemindersService
from backend.control_plane.schemas import ReminderToDeleteRequestSchema, \
    ReminderToEditTimeRequestSchema, ReminderToEditRequestSchema, ReminderSchema
from backend.control_plane.utils.auth import get_user_id_from_access_token

reminder_router = APIRouter(
    prefix="/reminder",
    tags=["Reminder"],
)


@reminder_router.post(
    path="/",
    responses={
        201: {
            "description": "Напоминание успешно создано"
        }
    }
)
async def reminder_add(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderSchema = Depends(),
        token: str = Depends(get_settings().OAUTH2_SCHEME)
) -> ReminderSchema:
    # TODO: try to call yandex gpt client
    # in client check global quota (maybe raise exception QuotaExceeded)
    # catch exceptions => return stupid reminder
    # success => return smart reminder
    user_id = get_user_id_from_access_token(token)
    reminder = await reminder_service.reminder_create(user_id=user_id, request=request)
    return reminder


@reminder_router.get(
    path="/",
    responses={
        200: {
            "description": "Список напоминаний"
        }
    }
)
async def reminders_get_active(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        token: str = Depends(get_settings().OAUTH2_SCHEME),
) -> Sequence[ReminderSchema]:
    user_id = get_user_id_from_access_token(token)
    reminders = await reminder_service.reminder_get_all_active(user_id=user_id)
    return reminders


@reminder_router.post(
    path="/{reminder_id}",
    responses={
        200: {
            "description": "Напоминание успешно обновлено"
        }
    }
)
async def reminder_edit(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderToEditRequestSchema = Depends(),
        token: str = Depends(get_settings().OAUTH2_SCHEME),
) -> ReminderSchema:
    user_id = get_user_id_from_access_token(token)

    reminder = await reminder_service.reminder_update(user_id=user_id, reminder=request)
    return reminder


@reminder_router.delete(
    path="/{reminder_id}",
    responses={
        204: {
            "description": "Напоминание успешно удалено"
        }
    }
)
async def reminder_delete(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderToDeleteRequestSchema = Depends(),
        token: str = Depends(get_settings().OAUTH2_SCHEME)
):
    user_id = get_user_id_from_access_token(token)

    await reminder_service.reminder_delete(user_id=user_id, reminder=request)
    return Response(status=204)


@reminder_router.post(
    path="/{reminder_id}/complete",
    responses={
        200: {
            "description": "Напоминание отмечено как выполненное"
        }
    }
)
async def reminder_to_complete(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderMarkAsCompleteRequestSchema = Depends(),
        token: str = Depends(get_settings().OAUTH2_SCHEME)
) -> ReminderSchema:
    user_id = get_user_id_from_access_token(token)
    reminder = await reminder_service.mark_as_complete(user_id=user_id, reminder=request)
    return reminder


@reminder_router.post(
    path="/{reminder_id}/postpone",
    responses={
        200: {
            "description": "Напоминание отложено"
        }
    }
)
async def reminder_postpone(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderToEditTimeRequestSchema = Depends(),
        token: str = Depends(get_settings().OAUTH2_SCHEME)
) -> ReminderSchema:
    user_id = get_user_id_from_access_token(token)
    reminder = await reminder_service.postpone(user_id=user_id, reminder=request)
    return reminder
