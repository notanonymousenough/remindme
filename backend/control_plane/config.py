import hashlib
from os import environ

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import PostgresDsn, computed_field, ConfigDict
from pydantic_core import MultiHostUrl
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

    DB_ADDRESS: str = environ.get("APP_ADDRESS", "127.0.0.1")

    SECRET_KEY: str = environ.get("SECRET_KEY", "")
    ALGORITHM: str = environ.get("ALGORITHM", "HS256")

    AUTH_COOKIE_NAME: str = "auth"

    POSTGRES_USER: str = environ.get("POSTGRES_USER")  # TELEGRAM SETTINGS
    POSTGRES_PASSWORD: str = environ.get("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = environ.get("POSTGRES_SERVER")
    POSTGRES_PORT: int = int(environ.get("POSTGRES_PORT"))
    POSTGRES_DB: str = environ.get("POSTGRES_DB")

    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    OAUTH2_SCHEME: OAuth2PasswordBearer = OAuth2PasswordBearer(
        tokenUrl=f"{APP_ADDRESS}:{APP_PORT}{PATH_PREFIX}/user/authentication")

    @computed_field  # type: ignore
    @property
    def bot_token_hash_bytes(self) -> bytes:
        return hashlib.sha256(self.BOT_TOKEN.encode()).digest()

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """
        Get uri for connection with database.
        """
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


def get_settings():
    return DefaultSettings()
