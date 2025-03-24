from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Path
from starlette import status

from backend.control_plane.db.init_db import create_tables, drop_tables
from backend.control_plane.schemas.reminder import ReminderSchema, ReminderSchemaToEdit, ReminderSchemaTime
from backend.control_plane.service.reminder_service import get_reminder_service, RemindersService

reminder_router = APIRouter(
    prefix="/reminder",
    tags=["Reminder"],
)


@reminder_router.get("/drop")  # временно
async def drop_tables_():
    await drop_tables()
    await create_tables()
    return "tables dropped"


@reminder_router.post("/")
async def reminder_add(
    request: ReminderSchema,
    reminder_service: Annotated[RemindersService, Depends(get_reminder_service)]
):
    reminder = await reminder_service.reminder_put(request)
    return reminder


@reminder_router.get("/")
async def reminders_get_all(
    reminder_service: Annotated[RemindersService, Depends(get_reminder_service)]
):
    reminders = await reminder_service.reminder_get_all()
    return reminders


@reminder_router.post("/{reminder_id}")
async def reminder_edit(
        request: ReminderSchemaToEdit,
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        reminder_id: UUID = Path(..., title="The ID of the reminder to edit")
):
    reminder = await reminder_service.reminder_update(reminder_id, **vars(request))
    return reminder


@reminder_router.delete("/{reminder_id}")
async def reminder_delete(
    reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
    reminder_id: UUID = Path(..., title="The ID of the reminder to delete")
):
    reminder = await reminder_service.reminder_delete(reminder_id)
    return reminder


@reminder_router.post("/{reminder_id}/complete")
async def reminder_to_complete(
    reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
    reminder_id: UUID = Path(..., title="The ID reminder to complete")
):
    reminder = await reminder_service.mark_as_complete(reminder_id)
    return reminder


@reminder_router.post("/{reminder_id}/postpone")
async def reminder_postpone(
        request: ReminderSchemaTime,
        reminder_service: Annotated[RemindersService, Depends(get_reminder_service)],
        reminder_id: UUID = Path(..., title="The ID reminder to postpone")
):
    reminder = await reminder_service.postpone(reminder_id=reminder_id, new_time=request.time)
    return reminder
