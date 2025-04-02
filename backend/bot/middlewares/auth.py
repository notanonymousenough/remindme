from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

from backend.bot.clients.remindme_api import RemindMeApiClient


class AuthMiddleware(BaseMiddleware):
    def __init__(self, api_client: RemindMeApiClient):  # Принимаем api_client в конструкторе
        self.api_client = api_client

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        """Middleware для авторизации пользователя."""
        user = event.from_user
        if not user:
            return  # Если нет пользователя (например, анонимный канал), пропускаем

        state: FSMContext = data.get('state')  # Получаем FSMContext из data
        if not state:
            print("FSMContext не найден в data.")
            return await handler(event, data)  # Если нет состояния, пропускаем middleware

        try:
            access_token = (await state.get_data())["access_token"]  # Пытаемся получить токен из состояния
        except:
            access_token = None
            print(f"AccessToken не найден в state для пользователя {user.id}. Проверяем API.")

        fields = "telegram_id", "first_name", "last_name", "username", "photo_url"
        request_data = {
            "telegram_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "photo_url": None
        }

        expected_access_token = await self.api_client.get_access_token(request_data)

        if access_token == expected_access_token:
            print(f"AccessToken cовпадает с существующим для {user.id}: {access_token}")
            return await handler(event, data)

        if expected_access_token:
            print(f"AccessToken получен из API для пользователя {user.id}: {expected_access_token}")
            await state.update_data(access_token=expected_access_token)  # Сохраняем токен в state
            data["state"] = state
            return await handler(event, data)  # Передаем управление handler'у

        print("Access token не получен с АПИ. Ошибка.")

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
