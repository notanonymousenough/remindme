from typing import Optional
from datetime import date, datetime
from enum import Enum as PyEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SexType(str, PyEnum):
    male = "male"
    female = "female"
    other = "other"


class UserSchema(BaseModel):
    """
    Схема данных пользователя.
    Описывает структуру данных для представления информации о пользователе.
    """
    id: Optional[UUID] = Field(None, description="Уникальный идентификатор пользователя в системе.")
    username: str = Field(..., description="Имя пользователя (логин) для идентификации.")
    email: Optional[str] = Field(None, description="Адрес электронной почты пользователя для связи и уведомлений.")
    sex: Optional[SexType] = Field(None, description="Пол пользователя")
    first_name: Optional[str] = Field(None, description="Имя пользователя.")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя.")
    birth_date: Optional[date] = Field(None, description="Дата рождения пользователя.")
    telegram_id: str = Field(None, description="Телеграм айди")
    calendar_integration_key: Optional[str] = Field(None, description="Calendar integration key")
    timezone: str = Field("UTC", description="Часовой пояс пользователя для локализации времени.")
    level: int = Field(1, description="level user")
    experience: int = Field(0, description="exp user")
    streak: int = Field(0, description="streak user")
    last_active: Optional[datetime] = Field(None,
                                            description="Временная метка последнего действия пользователя в системе.")

    class Config:
        from_attributes = True


class UserAddShema(BaseModel):
    id: Optional[UUID] = Field(None, description="Уникальный идентификатор пользователя в системе.")
    username: str = Field(..., description="Имя пользователя (логин) для идентификации.")
    telegram_id: str = Field(None, description="Телеграм айди")
    timezone: str = Field("UTC", description="Часовой пояс пользователя для локализации времени.")
    level: int = Field(1, description="level user")
    experience: int = Field(0, description="exp user")
    streak: int = Field(0, description="streak user")

    class Config:
        from_attributes = True


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
