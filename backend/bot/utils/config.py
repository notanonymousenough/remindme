from os import environ

from pydantic_settings import BaseSettings


class DefaultSettings(BaseSettings):
    """
    Default configs for application.
    """

    BOT_TOKEN: str = environ.get("BOT_TOKEN", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings():
    return DefaultSettings()
