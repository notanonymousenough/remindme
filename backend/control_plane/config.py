import hashlib
from datetime import timedelta, datetime
from os import environ

from fastapi.security import OAuth2PasswordBearer
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
    POSTGRES_DB: str = environ.get("POSTGRES_DB", '')

    # DEBUG MODE
    DEBUG: bool = True

    # JWT ENCODE SETTINGS
    SECRET_KEY: str = environ.get("SECRET_KEY", "")
    ALGORITHM: str = environ.get("ALGORITHM", "HS256")

    # BOT TOKEN FOR HASH GENERATION
    BOT_TOKEN: str = environ.get("BOT_TOKEN", "")

    # OAUTH2 SETTINGS
    JWT_TOKEN_LIFETIME: datetime = datetime.now() + timedelta(days=1)
    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    OAUTH2_SCHEME: OAuth2PasswordBearer = OAuth2PasswordBearer(
        scheme_name="TelegramAccessToken",
        tokenUrl=GET_ACCESS_TOKEN_ENDPOINT
    )

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


def get_settings():
    return DefaultSettings()
