from typing import Annotated

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from backend.bot.clients import get_client_async
from backend.bot.clients.remindme_api import RemindMeApiClient
from backend.bot.routers.tag_state_actions.get_tags import tags_get
from backend.bot.utils.depends import Depends
from backend.bot.utils.states import States

delete_tag_router = Router()


@delete_tag_router.callback_query(StateFilter(States.reminder_menu),
                                F.data.startswith("tag_delete"))
async def tag_edit_process_0(call: CallbackQuery,
                             state: FSMContext,
                             client=Annotated[
                                 RemindMeApiClient, Depends(get_client_async)]):
    data = await state.get_data()
    access_token = data["access_token"]
    tag_id = data["tag_edit_process_ID"]

    if await client().tag_delete(access_token=access_token, tag_id=tag_id):
        text = "*Тэг успешно удален!*\n\n"
    else:
        text = "*ОШИБКА ПРИ ОТПРАВКЕ НА СЕРВЕР*\n\n"
    await tags_get(message=call.message, state=state, text=text)
