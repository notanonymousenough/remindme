from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, CallbackQuery


class IgnoreMessageNotModifiedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # Проверяем, является ли event объектом CallbackQuery
                if isinstance(event, CallbackQuery):
                    call = event  # Теперь у нас есть доступ к объекту CallbackQuery как 'call'
                    bot: Bot = data.get("bot")  # Получаем объект Bot из data, предполагая что он там есть.
                    if bot:
                        await bot.answer_callback_query(call.id)
                        return None  # Игнорируем исключение после отправки answer_callback_query
                    else:
                        print("Warning: Bot object not found in data, cannot answer callback query.")
                        return None  # Игнорируем исключение, но не смогли ответить на callback
                else:
                    # Если это не CallbackQuery, просто игнорируем исключение (или обрабатываем иначе по необходимости)
                    return None
            else:
                # Перевыбрасываем исключение, если это другая ошибка TelegramBadRequest
                raise e