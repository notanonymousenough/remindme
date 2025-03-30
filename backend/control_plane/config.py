import hashlib
from os import environ

from fastapi.openapi.models import OAuthFlowClientCredentials, OAuthFlows, OAuthFlowPassword
from fastapi.security import OAuth2PasswordBearer, OAuth2, OAuth2AuthorizationCodeBearer
from passlib.context import CryptContext
from pydantic import computed_field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

from backend.control_plane.schemas.user import UserTelegramDataSchema

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

    AUTH_COOKIE_NAME: str = "auth"

    POSTGRES_USER: str = environ.get("POSTGRES_USER", 'postgres')
    POSTGRES_PASSWORD: str = environ.get("POSTGRES_PASSWORD", 'postgres')
    POSTGRES_ADDRESS: str = environ.get("POSTGRES_ADDRESS", '127.0.0.1')
    POSTGRES_PORT: int = int(environ.get("POSTGRES_PORT", '5432'))
    POSTGRES_DB: str = environ.get("POSTGRES_DB", '')

    BOT_TOKEN: str = environ.get("BOT_TOKEN", "")

    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    OAUTH2_SCHEME: OAuth2 = OAuth2(
        scheme_name="UserTelegramDataSchema",
        flows=OAuthFlows(password=OAuthFlowPassword(tokenUrl=f"{APP_ADDRESS}:{APP_PORT}{PATH_PREFIX}/auth/telegram")),
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
