from aiogram.fsm.context import FSMContext

from backend.bot.clients import get_client_async


async def state_data_reset(state: FSMContext, telegram_id: int, access_token: str):
    await state.set_data({
        "day": "today",
        "user_id": telegram_id,
        "day_filter": "today",
        "next_coef": 0,
        "strip": [0, 5],
        "tag_filter_click": 0,
        "tag_filter": None,
        "add_reminder": 0,
        "access_token": access_token,
        "new_tag_review": False,
        "new_tag_emoji": None
    })
