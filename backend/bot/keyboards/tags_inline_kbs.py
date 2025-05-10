from typing import Sequence

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from backend.control_plane.config import get_settings
from backend.control_plane.schemas.tag import TagSchema


def tag_menu_get_tags(tags: Sequence[TagSchema]):
    keyboard = InlineKeyboardBuilder()

    for i, tag in enumerate(tags):  # for tag in tags.keys()
        keyboard.add(InlineKeyboardButton(text=str(i + 1), callback_data=f"tag_edit_id_{str(tag.id)}"))
    if len(tags) < get_settings().TAGS_MAX_LENGTH:
        keyboard.row(InlineKeyboardButton(text='Добавить новый тэг', callback_data=f"tag_new"))

    return keyboard.as_markup()


def tag_edit_menu_get_actions():
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Имя", callback_data=f"tag_edit_action_NAME"))
    keyboard.add(InlineKeyboardButton(text='Эмодзи', callback_data=f"tag_edit_action_EMOJI"))

    return keyboard.as_markup()


def get_tag_review_buttons():
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text="Да, добавить", callback_data=f"new_tag_process_True"))
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data=f"new_tag_process_False"))

    return keyboard.as_markup()
