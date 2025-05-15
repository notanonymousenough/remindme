import asyncio
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.control_plane.app import get_app
from backend.control_plane.db.engine import get_async_session
from backend.control_plane.db.models import HabitPeriod, UserAchievement, AchievementCategory, AchievementTemplate
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.achievementschema import AchievementSchema
from backend.control_plane.schemas.auth import UserTelegramDataSchema
from backend.control_plane.schemas.habit import HabitSchemaResponse
from backend.control_plane.schemas.requests.habit import HabitPostRequest


@pytest.fixture(scope="class")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Override the default pytest-asyncio event_loop fixture to be class-scoped."""
    print("\n--- Setting up class-scoped event loop ---")  # Отладочный вывод
    loop = asyncio.new_event_loop()
    yield loop
    print("--- Closing class-scoped event loop ---")  # Отладочный вывод
    loop.close()


@pytest.fixture(name="session", scope="function")
async def session() -> AsyncGenerator[AsyncSession | Any, Any]:
    """
    СЕССИЯ ДЛЯ ВЗАИМОДЕЙСТВИЯ С БД
    """
    yield get_async_session()


@pytest.fixture(name="client", scope="class")
async def client() -> AsyncClient:
    """
    КЛИЕНТ ДЛЯ ВЗАИМОДЕЙСТВИЯ С АПИ
    """
    app = get_app()
    # utils_module.check_website_exist = AsyncMock(return_value=(True, "Status code < 400"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac  # Yield'им сам клиент


# --- Фикстуры для создания тестовых данных ---

# Фикстура для создания тестового пользователя
@pytest.fixture(name="auth_user", scope="class")
async def auth_user(client) -> AsyncGenerator[Any, Any]:
    """
    ВОЗВРАЩАЕТ headers С ТОКЕНОМ АВТОРИЗАЦИИ
    """
    user = UserTelegramDataSchema.model_validate({
        "id": "12345",  # telegram id
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "auth_date": str((datetime.now() + timedelta(hours=10)).isoformat()),
        "hash": "huizxc"
    })
    user.auth_date = int(user.auth_date.timestamp())
    auth_response = await client.post(url="/v1/auth/telegram", json=user.model_dump())
    if auth_response.status_code == status.HTTP_200_OK:
        auth_headers = {
            "Authorization": f"{auth_response.json()['token_type'].title()} {auth_response.json()['access_token']}"
        }
        yield auth_headers
    else:
        raise Exception(auth_response.status_code, auth_response.content)

    print("\nINFO: УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ")
    response = await client.delete(url="/v1/user/", headers=auth_headers)
    assert response.status_code == 200


@pytest.fixture(name="TestReminder", scope="function")
async def TestReminder(client, auth_user):
    """
    ПОЛУЧЕНИЕ СЛУЧАЙНОГО НАПОМИНАНИЯ КОТОРОЕ ЕСТЬ В БД
    ЕСЛИ НЕТ, СОЗДАЕТ И ВОЗВРАЩАЕТ
    """
    user = await client.get("/v1/user/", headers=auth_user)

    response_reminders = await client.get("/v1/reminder/", headers=auth_user)
    if response_reminders.json():
        reminder = ReminderSchema.model_validate(response_reminders.json()[0])
        yield reminder
    else:
        reminder_json = {
            "text": "reminderTest0",
            "time": str((datetime.now() + timedelta(hours=10)).isoformat()),
            "tags": [],
            "user_id": user.json()["id"]
        }
        response = await client.post("/v1/reminder/", headers=auth_user, json=reminder_json)
        reminder = ReminderSchema.model_validate(response.json())
        yield reminder

@pytest.fixture(name="TestHabit", scope="function")
async def TestHabit(client, auth_user):
    """
    ПОЛУЧЕНИЕ СЛУЧАЙНОЙ ПРИВЫЧКИ КОТОРОЕ ЕСТЬ В БД
    ЕСЛИ НЕТ, СОЗДАЕТ И ВОЗВРАЩАЕТ
    """
    habit_response = await client.get("/v1/habit/", headers=auth_user)
    if habit_response.json():
        habit = HabitSchemaResponse.model_validate(habit_response.json()[0])
        yield habit
    else:
        habit_request = {
            "text": "habitTest0",
            "interval": HabitPeriod.WEEKLY
        }
        habit = HabitPostRequest.model_validate(habit_request)
        response = await client.post("/v1/habit/", headers=auth_user, data=habit.model_dump_json())

        habit = HabitSchemaResponse.model_validate(response.json())
        yield habit

@pytest.fixture(name="TestAchievement", scope="function")
async def TestAchievement(session, client, auth_user):
    user = await client.get("/v1/user/", headers=auth_user)
    achievement = {
            "user_id": user.json()["id"],
            "template_id": None,
            "unlocked": True,
            "unlocked_at": datetime.now(),
            "progress": 100,
            "updated_at": datetime.now(),
            "created_at": datetime.now() - timedelta(days=10)
        }
    achievement_template = {
        "name": "Заходить в нашего телеграм бота миллиард раз",
        "description": "Для самых преданных",
        "condition": "active",
        "category": AchievementCategory.SYSTEM
    }
    async with await session as session:
        achievement_template_model = AchievementTemplate(**achievement_template)
        session.add(achievement_template_model)
        await session.commit()
        await session.refresh(achievement_template_model)

        achievement["template_id"] = achievement_template_model.id
        achievement_model = UserAchievement(**achievement)
        session.add(achievement_model)
        await session.commit()

        await session.refresh(achievement_model)
        yield AchievementSchema.model_validate(achievement_model)
