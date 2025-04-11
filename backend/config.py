import hashlib
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

    PATH_PREFIX: str = environ.get("PATH_PREFIX", "")
    APP_ADDRESS: str = environ.get("APP_ADDRESS", "127.0.0.1")
    APP_PORT: int = int(environ.get("APP_PORT", 8000))

    SECRET_KEY: str = environ.get("SECRET_KEY", "")
    ALGORITHM: str = environ.get("ALGORITHM", "HS256")

    GET_ACCESS_TOKEN_ENDPOINT: str = "/auth/telegram"

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

    BOT_TOKEN: str = environ.get("BOT_TOKEN", "")

    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Настройки Temporal
    TEMPORAL_HOST: str = environ.get("TEMPORAL_HOST", "localhost:7233")
    TEMPORAL_NAMESPACE: str = environ.get("TEMPORAL_NAMESPACE", "remindme")
    TEMPORAL_TASK_QUEUE: str = environ.get("TEMPORAL_TASK_QUEUE", "remindme-tasks")
    ACTIVE_REMINDERS_LIMIT: int = environ.get("ACTIVE_REMINDERS_LIMIT", 1000)

    # Настройки Telegram
    TELEGRAM_BOT_TOKEN: str = environ.get("BOT_TOKEN", "")
    TELEGRAM_API_URL: str = "https://api.telegram.org/bot"

    # Настройки Yandex GPT
    YANDEX_GPT_API_KEY: str = environ.get("YANDEX_GPT_API_KEY", "")
    YANDEX_GPT_API_URL: str = "https://api.yacloud.yandex.ru/gpt/v1/generation"
    YANDEX_GPT_IMAGE_URL: str = "https://api.yacloud.yandex.ru/gpt/v1/image/generation"

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
            tokenUrl=f"{self.APP_ADDRESS}:{self.APP_PORT}{self.PATH_PREFIX}/auth/telegram"
        )


def get_settings():
    return DefaultSettings()
