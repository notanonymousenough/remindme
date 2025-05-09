from aiogram.fsm.context import FSMContext

from backend.bot.clients import get_client_async


async def state_data_reset(state: FSMContext, telegram_id: int, access_token: str, timezone):
    """
    Reset data in state
    """
    await state.set_data({
        "timezone": timezone,
        "day": "today",
        "user_id": telegram_id,
        "day_filter": "today",
        "next_coef": 0,
        "strip": [0, 5],
        "tag_filter_click": False,
        "tag_filter": None,
        "add_reminder": False,
        "add_reminder_manual": False,
        "add_reminder_manual_reminder_text": None,
        "access_token": access_token,  # access_token
        "new_tag_review": False,  # new_tag
        "new_tag_emoji": None,
        "reminder_id": None,  # edit_reminder
        'mode': [],
        "habit_name": None,  # edit habit
    })