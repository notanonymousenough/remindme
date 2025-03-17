from typing import Annotated, Sequence

from aiohttp.web_response import Response
from fastapi import APIRouter, Depends

from backend.control_plane.db.init_db import create_tables, drop_tables
from backend.control_plane.service.reminder_service import get_reminder_service, RemindersService
from backend.control_plane.schemas import ReminderToDeleteRequestSchema, \
    ReminderToCompleteRequestSchema, ReminderToEditTimeRequestSchema, ReminderToEditRequestSchema, ReminderSchema

reminder_router = APIRouter(
    prefix="/reminder",
    tags=["Reminder"],
)


@reminder_router.get("/drop")  # временно
async def drop_tables_():
    await drop_tables()
    await create_tables()
    return "tables dropped"


@reminder_router.post(
    path="/",
    responses={
        201: {
            "description": "Напоминание успешно создано",
            "content": {
                "application/json": {
                    "schema": ReminderSchema.model_json_schema()
                }
            }
        }
    }
)
async def reminder_add(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderSchema = Depends()
) -> ReminderSchema:
    # TODO: try to call yandex gpt client
    # in client check global quota (maybe raise exception QuotaExceeded)
    # catch exceptions => return stupid reminder
    # success => return smart reminder
    reminder = await reminder_service.reminder_create(request)
    return reminder


@reminder_router.get(
    path="/",
    responses={
        200: {
            "description": "Список напоминаний",
            "content": {
                "application/json": {
                    "schema": Sequence[ReminderSchema.model_json_schema()]
                }
            }
        }
    }
)
async def reminders_get_all(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)]
) -> Sequence[ReminderSchema]:
    reminders = await reminder_service.reminder_get_all()
    return reminders


@reminder_router.post(
    path="/{reminder_id}",
    responses={
        200: {
            "description": "Напоминание успешно обновлено",
            "content": {
                "application/json": {
                    "schema": ReminderSchema.model_json_schema()
                }
            }
        }
    }
)
async def reminder_edit(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderToEditRequestSchema = Depends()
) -> ReminderSchema:
    reminder = await reminder_service.reminder_update(reminder=request)
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
        request: ReminderToDeleteRequestSchema = Depends()
) -> Response:
    await reminder_service.reminder_delete(reminder=request)
    return Response(status=204)


@reminder_router.post(
    path="/{reminder_id}/complete",
    responses={
        200: {
            "description": "Напоминание отмечено как выполненное",
            "content": {
                "application/json": {
                    "schema": ReminderSchema.model_json_schema()
                }
            }
        }
    }
)
async def reminder_to_complete(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderToCompleteRequestSchema = Depends()
) -> ReminderSchema:
    reminder = await reminder_service.mark_as_complete(reminder=request)
    return reminder


@reminder_router.post(
    path="/{reminder_id}/postpone",
    responses={
        200: {
            "description": "Напоминание отложено",
            "content": {
                "application/json": {
                    "schema": ReminderSchema.model_json_schema()
                }
            }
        }
    }
)
async def reminder_postpone(
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        request: ReminderToEditTimeRequestSchema = Depends()
) -> ReminderSchema:
    reminder = await reminder_service.postpone(reminder=request)
    return reminder
