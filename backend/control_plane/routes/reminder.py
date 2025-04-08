from typing import Annotated, Sequence
from uuid import UUID

from aiohttp.web_response import Response
from fastapi import APIRouter, Depends, Body

from backend.control_plane.schemas.requests.reminder import ReminderMarkAsCompleteRequestSchema, \
    ReminderAddSchemaRequest
from backend.control_plane.schemas.user import UserSchema
from backend.control_plane.service.reminder_service import get_reminder_service, RemindersService
from backend.control_plane.schemas import ReminderToEditTimeRequestSchema, ReminderToEditRequestSchema, ReminderSchema
from backend.control_plane.utils.auth import get_authorized_user

reminder_router = APIRouter(
    prefix="/reminder",
    tags=["Reminder"],
)


@reminder_router.post(
    path="/",
    responses={
        200: {
            "description": "Напоминание успешно создано"
        }
    }
)
async def reminder_add(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderAddSchemaRequest = Body(...),
        user: UserSchema = Depends(get_authorized_user)
) -> ReminderSchema:
    # TODO: try to call yandex gpt client
    # in client check global quota (maybe raise exception QuotaExceeded)
    # catch exceptions => return stupid reminder
    # success => return smart reminder
    reminder = await reminder_service.reminder_create(user_id=user.id, reminder=request)
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
        user: UserSchema = Depends(get_authorized_user)
) -> Sequence[ReminderSchema]:
    reminders = await reminder_service.reminders_get_active(user_id=user.id)
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
        request: ReminderToEditRequestSchema = Body(...),
        user: UserSchema = Depends(get_authorized_user)
) -> ReminderSchema:
    reminder = await reminder_service.reminder_update(user_id=user.id, reminder=request)
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
        reminder_id: UUID,
        user: UserSchema = Depends(get_authorized_user)
):
    if await reminder_service.reminder_delete(user_id=user.id, reminder_id=reminder_id):
        return Response(status=204, text=f"Успешно удалено {reminder_id}")
    return Response(status=404, text="Напоминание не удалено")


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
        request: ReminderMarkAsCompleteRequestSchema = Body(...),
        user: UserSchema = Depends(get_authorized_user)
) -> ReminderSchema:
    reminder = await reminder_service.mark_as_complete(user_id=user.id, reminder=request)
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
        request: ReminderToEditTimeRequestSchema = Body(...),
        user: UserSchema = Depends(get_authorized_user)
) -> ReminderSchema:
    reminder = await reminder_service.postpone(user_id=user.id, reminder=request)
    return reminder
