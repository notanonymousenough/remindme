"""
Конфигурация для data-plane сервиса
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения"""

    # Настройки Temporal
    TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "localhost:7233")
    TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "remindme")
    TEMPORAL_TASK_QUEUE: str = os.getenv("TEMPORAL_TASK_QUEUE", "remindme-tasks")
    ACTIVE_REMINDERS_LIMIT: int = os.getenv("ACTIVE_REMINDERS_LIMIT", 1000)

    # Настройки Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot"

    # Настройки Yandex GPT
    YANDEX_GPT_API_KEY: str = os.getenv("YANDEX_GPT_API_KEY", "")
    YANDEX_GPT_API_URL: str = "https://api.yacloud.yandex.ru/gpt/v1/generation"
    YANDEX_GPT_IMAGE_URL: str = "https://api.yacloud.yandex.ru/gpt/v1/image/generation"

    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Настройки сервиса
    APP_NAME: str = "remindme-data-plane"
    APP_VERSION: str = "0.1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # TODO: fix
        extra = "allow"


settings = Settings()
