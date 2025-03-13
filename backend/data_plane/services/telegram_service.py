"""
Сервис для работы с Telegram API
"""
import aiohttp
import logging
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("telegram_service")


class TelegramService:
    """Сервис для отправки сообщений через Telegram Bot API"""

    def __init__(self):
        """Инициализация сервиса"""
        self.api_url = f"{settings.TELEGRAM_API_URL}{settings.TELEGRAM_BOT_TOKEN}"

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
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"Ошибка отправки сообщения в Telegram: {response.status} - {response_text}")
                        return False
        except Exception as e:
            logger.error(f"Исключение при отправке сообщения в Telegram: {str(e)}")
            return False
