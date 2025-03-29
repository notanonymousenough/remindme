from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable


class AuthMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        """computed_hash = hmac.new(
            secret_key,  # bot_token
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()"""  # control_plane...utils.auth


        # 1) Check AccessToken in state, if exists -> ok
        # 2) Get AccessToken in remindme api, if exists -> ok
        # state.set("token"=data.get_state())
        # 3) Process user registration -> hash_generate()





        result = await handler(event, data)
        return result
