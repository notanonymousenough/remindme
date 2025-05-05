import hashlib
from datetime import timedelta, datetime
from os import environ

from passlib.context import CryptContext
from pydantic import computed_field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные окружения из файла .env в os.environ


class DefaultSettings(BaseSettings):
    """
    Default configs for application.
    """

    model_config = ConfigDict(
        extra="allow"
    )

    # WEB ADDRESS
    APP_ADDRESS: str = environ.get("APP_ADDRESS", "127.0.0.1")
    APP_PORT: int = int(environ.get("APP_PORT", 8000))
    PATH_PREFIX: str = environ.get("PATH_PREFIX", "/v1")
    FULL_ADDRESS: str = f"http://{APP_ADDRESS}:{APP_PORT}{PATH_PREFIX}/"  # without SSL

    # ENDPOINTS
    GET_ACCESS_TOKEN_ENDPOINT: str = "auth/telegram"

    # REMINDER ENDPOINTS
    GET_REMINDERS_ENDPOINT: str = "reminder/"
    GET_REMINDER_ENDPOINT: str = "reminder/{id}/"
    POST_REMINDER_ENDPOINT: str = "reminder/"
    DELETE_REMINDER_ENDPOINT: str = "reminder/{id}"
    COMPLETE_REMINDER_ENDPOINT: str = "reminder/{id}/complete"
    POSTPONE_REMINDER_ENDPOINT: str = "reminder/{id}/postpone"

    # TAG ENDPOINTS
    GET_TAGS_ENDPOINT: str = "tag/"
    POST_TAG_ENDPOINT: str = "tag/"
    DELETE_TAG_ENDPOINT: str = "tag/{id}/"

    # HABIT ENDPOINTS
    GET_HABITS_ENDPOINT: str = "habit/"
    POST_HABIT_ENDPOINT: str = "habit/"
    DELETE_HABIT_ENDPOINT: str = "habit/{id}/"
    PUT_HABIT_ENDPOINT: str = "habit/{id}/"
    POST_HABIT_PROGRESS_ENDPOINT: str = "habit/{id}/progress/"

    # POSTGRES INFO
    POSTGRES_USER: str = environ.get("POSTGRES_USER", 'postgres')
    POSTGRES_PASSWORD: str = environ.get("POSTGRES_PASSWORD", 'postgres')
    POSTGRES_ADDRESS: str = environ.get("POSTGRES_ADDRESS", '127.0.0.1')
    POSTGRES_PORT: int = int(environ.get("POSTGRES_PORT", '5432'))
    POSTGRES_DB: str = environ.get("POSTGRES_DB", 'remind_me')

    SQL_ECHO: bool = environ.get("SQL_ECHO", "False").lower() in ("true", "1", "t")
    SQL_POOL_SIZE: int = environ.get("SQL_POOL_SIZE", "5")
    SQL_MAX_OVERFLOW: int = environ.get("SQL_MAX_OVERFLOW", "10")
    SQL_POOL_TIMEOUT: int = environ.get("SQL_POOL_TIMEOUT", "30")
    SQL_POOL_RECYCLE: int = environ.get("SQL_POOL_RECYCLE", "1800")

    DEBUG: bool = environ.get("DEBUG", "false").lower() in ("true", "1", "t")

    # JWT ENCODE SETTINGS
    SECRET_KEY: str = environ.get("SECRET_KEY", "")
    ALGORITHM: str = environ.get("ALGORITHM", "HS256")

    # BOT TOKEN FOR HASH GENERATION
    BOT_TOKEN: str = environ.get("BOT_TOKEN", "")

    # OAUTH2 SETTINGS
    JWT_TOKEN_LIFETIME: datetime = timedelta(days=1)
    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # CONSTANTS
    TAGS_MAX_LENGTH: int = 7  # for bot inline keyboard

    # Настройки Temporal
    TEMPORAL_HOST: str = environ.get("TEMPORAL_HOST", "localhost:7233")
    TEMPORAL_NAMESPACE: str = environ.get("TEMPORAL_NAMESPACE", "remindme")
    TEMPORAL_TASK_QUEUE: str = environ.get("TEMPORAL_TASK_QUEUE", "remindme-tasks")
    ACTIVE_REMINDERS_LIMIT: int = environ.get("ACTIVE_REMINDERS_LIMIT", 1000)
    CLEANUP_DAYS_THRESHOLD: int = environ.get("CLEANUP_DAYS_THRESHOLD", 10)
    HABIT_IMAGE_CHARACTER: str = environ.get("HABIT_IMAGE_CHARACTER", "кот")

    # Настройки Telegram
    TELEGRAM_BOT_TOKEN: str = environ.get("BOT_TOKEN", "")
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot"

    # Настройки Yandex GPT
    YANDEX_GPT_MODEL_NAME: str = environ.get("YANDEX_GPT_MODEL_NAME", "yandexgpt-lite")
    YANDEX_GPT_MODEL_COST: float = environ.get("YANDEX_GPT_MODEL_COST", 0.2)
    YANDEX_CLOUD_AI_SECRET: str = environ.get("YANDEX_CLOUD_AI_SECRET", "")
    YANDEX_CLOUD_S3_BUCKET_NAME: str = environ.get("YANDEX_CLOUD_S3_BUCKET_NAME", "remindme-images-bucket")
    YANDEX_CLOUD_S3_KEY_ID: str = environ.get("YANDEX_CLOUD_S3_KEY_ID", "")
    YANDEX_CLOUD_S3_SECRET: str = environ.get("YANDEX_CLOUD_S3_SECRET", "")
    YANDEX_CLOUD_FOLDER: str = environ.get("YANDEX_CLOUD_FOLDER", "")
    YANDEX_ART_MODEL_COST: float = 2.2

    # Настройки логирования
    LOG_LEVEL: str = environ.get("LOG_LEVEL", "INFO")

    @computed_field  # type: ignore
    @property
    def bot_token_hash_bytes(self) -> bytes:
        return hashlib.sha256(self.BOT_TOKEN.encode()).digest()

    @property
    def DATABASE_URI(self) -> str:
        return (f"postgresql+asyncpg://"
                f"{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_ADDRESS}/"
                f"{self.POSTGRES_DB}")

    @property
    def OAUTH2_SCHEME(self):
        from fastapi.security import OAuth2PasswordBearer
        return OAuth2PasswordBearer(
            scheme_name="TelegramAccessToken",
            tokenUrl=self.GET_ACCESS_TOKEN_ENDPOINT
        )


def get_settings():
    return DefaultSettings()
