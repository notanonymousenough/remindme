"""
Сервис для работы с Telegram API
"""
import aiohttp
import logging
import json
from typing import Dict, Any, Optional
from backend.config import get_settings
import certifi
import ssl

logger = logging.getLogger("telegram_service")
ssl_context = ssl.create_default_context(cafile=certifi.where())


class TelegramService:
    """Сервис для отправки сообщений через Telegram Bot API"""

    def __init__(self):
        """Инициализация сервиса"""
        self.api_url = f"{get_settings().TELEGRAM_API_URL}{get_settings().TELEGRAM_BOT_TOKEN}"

    async def send_message(
            self,
            chat_id: str,
            text: str,
            reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Отправляет сообщение пользователю через Telegram

        Args:
            chat_id: ID чата/пользователя
            text: Текст сообщения
            reply_markup: Клавиатура (кнопки)

        Returns:
            bool: Успешность отправки
        """
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, ssl=ssl_context) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise ValueError(f"Ошибка отправки сообщения в Telegram: {response.status} - {response_text}")

                return True
