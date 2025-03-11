from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable


class AuthMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        # 1) Check AccessToken in state, if exists -> ok
        # 2) Get AccessToken in remindme api, if exists -> ok
        # 3) Process user registration
        result = await handler(event, data)
        return result
