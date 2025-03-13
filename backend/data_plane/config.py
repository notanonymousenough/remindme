"""
Конфигурация для data-plane сервиса
"""
import os
from pydantic import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения"""
    # Настройки базы данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/remind_me")

    # Настройки Temporal
    TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "localhost:7233")
    TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "remind-me")
    TEMPORAL_TASK_QUEUE: str = os.getenv("TEMPORAL_TASK_QUEUE", "remind-me-tasks")

    # Настройки Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot"

    # Настройки Yandex GPT
    YANDEX_GPT_API_KEY: str = os.getenv("YANDEX_GPT_API_KEY", "")
    YANDEX_GPT_API_URL: str = "https://api.yacloud.yandex.ru/gpt/v1/generation"
    YANDEX_GPT_IMAGE_URL: str = "https://api.yacloud.yandex.ru/gpt/v1/image/generation"

    # Настройки обслуживания
    CLEANUP_DAYS_THRESHOLD: int = int(os.getenv("CLEANUP_DAYS_THRESHOLD", "30"))

    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Настройки сервиса
    APP_NAME: str = "remind-me-data-plane"
    APP_VERSION: str = "0.1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
