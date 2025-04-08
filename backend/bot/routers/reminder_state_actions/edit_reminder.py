from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from backend.bot import bot
from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.utils import States

from backend.bot.utils.depends import Depends

edit_reminder_router = Router(name="edit_reminder_router")


@edit_reminder_router.callback_query(StateFilter(States.reminder_menu),
                                 F.data.startswith("reminder_edit_"))
async def reminder_edit(call: CallbackQuery,
                        state: FSMContext,
                        client=Annotated[RemindMeApiClient, Depends(get_client_async)]):

    # TODO
    await bot.answer_callback_query(call.id)
