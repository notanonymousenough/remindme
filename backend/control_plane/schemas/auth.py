from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserTelegramDataSchema(BaseModel):
    id: str = Field(None, description="Телеграм айди")  # telegram id
    first_name: Optional[str] = Field(None, description="first name")
    last_name: Optional[str] = Field(None, description="last name")
    username: str = Field(..., description="Имя пользователя (логин) для идентификации.")
    photo_url: Optional[str] = Field(None, description="photo url")
    auth_date: datetime = Field(..., description="дата авторизации")
    hash: str = Field(..., description="хэш токен")

    class Config:
        from_attributes = True
