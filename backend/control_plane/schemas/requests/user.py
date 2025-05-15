from datetime import date, datetime
from typing import Optional
from uuid import UUID
from fastapi.params import Path

from pydantic import BaseModel, Field

from backend.control_plane.schemas.user import SexType


class UserUpdateRequest(BaseModel):
    """
    Схема данных пользователя.
    Описывает структуру данных для представления информации о пользователе.
    """
    id: Optional[UUID] = Path(..., description="Уникальный идентификатор пользователя в системе.")
    username: str = Field(None, description="Имя пользователя (логин) для идентификации.")
    email: Optional[str] = Field(None, description="Адрес электронной почты пользователя для связи и уведомлений.")
    sex: Optional[SexType] = Field(None, description="Пол пользователя")
    first_name: Optional[str] = Field(None, description="Имя пользователя.")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя.")
    birth_date: Optional[date] = Field(None, description="Дата рождения пользователя.")
    telegram_id: str = Field(None, description="Телеграм айди")
    calendar_integration_key: Optional[str] = Field(None, description="Calendar integration key")
    timezone: str = Field(None, description="Часовой пояс пользователя для локализации времени.")

    class Config:
        from_attributes = True


class UserUpdateTimezoneRequest:
    id: Optional[UUID] = Field(None, description="ID")
    timezone: Optional[str] = Field(..., description="Timezone")

    class Config:
        from_attributes = True