from os import environ

from passlib.context import CryptContext
from pydantic_settings import BaseSettings


class DefaultSettings(BaseSettings):
    """
    Default configs for application.
    """

    PATH_PREFIX: str = environ.get("PATH_PREFIX", "")
    APP_ADDRESS: str = environ.get("APP_ADDRESS", "127.0.0.1")
    APP_PORT: int = int(environ.get("APP_PORT", 8000))

    DB_ADDRESS: str = environ.get("APP_ADDRESS", "127.0.0.1")

    SECRET_KEY: str = environ.get("SECRET_KEY", "")
    ALGORITHM: str = environ.get("ALGORITHM", "HS256")

    @property
    def database_uri(self) -> str:
        """
        Get uri for connection with database.
        """
        return ""


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings():
    return DefaultSettings()
