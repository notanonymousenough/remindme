"""
Сервис для работы с Yandex GPT API
"""
import aiohttp
import logging
import json
from typing import Dict, Any
from ..config import settings

logger = logging.getLogger("yandex_gpt_service")


class YandexGPTService:
    """Сервис для взаимодействия с Yandex GPT API"""

    def __init__(self):
        """Инициализация сервиса"""
        self.api_key = settings.YANDEX_GPT_API_KEY
        self.text_url = settings.YANDEX_GPT_API_URL
        self.image_url = settings.YANDEX_GPT_IMAGE_URL

    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Генерирует текст с помощью Yandex GPT

        Args:
            prompt: Текстовый промпт
            max_tokens: Максимальное количество токенов

        Returns:
            Dict: Результат генерации
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }

        data = {
            "modelUri": "gpt://b1g8k2h4cncvh4ghl4q1/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": max_tokens
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.text_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "text": result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text",
                                                                                                                 "")
                        }
                    else:
                        response_text = await response.text()
                        logger.error(f"Ошибка генерации текста: {response.status} - {response_text}")
                        return {
                            "success": False,
                            "error": f"Error {response.status}: {response_text}"
                        }
        except Exception as e:
            logger.error(f"Исключение при генерации текста: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_image(self, prompt: str) -> Dict[str, Any]:
        """
        Генерирует изображение с помощью Yandex GPT

        Args:
            prompt: Текстовый промпт для генерации изображения

        Returns:
            Dict: Результат генерации с URL изображения
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }

        data = {
            "modelUri": "gpt://b1g8k2h4cncvh4ghl4q1/image-generation",
            "completionOptions": {
                "imageSize": "1024x1024"
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.image_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        image_url = result.get("result", {}).get("images", [None])[0]
                        if image_url:
                            # Создаем миниатюру из основного изображения
                            thumbnail_url = image_url  # В реальности здесь было бы создание миниатюры

                            return {
                                "success": True,
                                "image_url": image_url,
                                "thumbnail_url": thumbnail_url
                            }
                        else:
                            return {
                                "success": False,
                                "error": "No image URL in response"
                            }
                    else:
                        response_text = await response.text()
                        logger.error(f"Ошибка генерации изображения: {response.status} - {response_text}")
                        return {
                            "success": False,
                            "error": f"Error {response.status}: {response_text}"
                        }
        except Exception as e:
            logger.error(f"Исключение при генерации изображения: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
