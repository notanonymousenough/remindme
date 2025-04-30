import os
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator
from uuid import uuid4

# Импортируем наш основной app и модели/схемы
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.control_plane.app import get_app
from backend.control_plane.config import get_settings
from backend.control_plane.db.engine import get_async_session
from backend.control_plane.schemas import ReminderSchema
from backend.control_plane.schemas.user import UserTelegramDataSchema


@pytest.fixture(name="sqlite")
async def sqlite() -> str:
    """
    Создает временную БД для запуска теста.
    """
    settings = get_settings()

    tmp_name = ".".join([uuid4().hex, "pytest"])
    settings.DB_NAME = tmp_name
    os.environ["DB_NAME"] = tmp_name

    try:
        yield settings.database_uri
    finally:
        os.remove(tmp_name)


@pytest.fixture(name="database")
async def database(sqlite) -> AsyncSession:
    """
    Returns a class object with which you can create a new session to connect to the database.
    """
    async with get_async_session() as session:
        yield session


@pytest.fixture(name="client")
async def client(database) -> AsyncClient:
    """
    Returns a client that can be used to interact with the application.
    """
    app = get_app()
    # utils_module.check_website_exist = AsyncMock(return_value=(True, "Status code < 400"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac  # Yield'им сам клиент


# --- Фикстуры для создания тестовых данных ---

# Фикстура для создания тестового пользователя
@pytest.fixture(name="auth_user")
async def auth_user(client) -> AsyncGenerator[Any, Any]:
    user = {
        "telegram_id": 12345,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "created_at": datetime.utcnow(), # Убедись, что datetime импортирован
        "updated_at": datetime.utcnow()
    }
    auth_response = await client.post(url="/v1/user/auth", json=user)
    if auth_response.status_code == status.HTTP_201_CREATED:
        yield auth_response.json()
    raise Exception(auth_response.status_code, auth_response.content)

@pytest.fixture(scope="function")
def test_reminder(client) -> ReminderSchema:
    reminder = {
        "text": "reminderTest0",
        "time": datetime.now() + timedelta(hours=10),
        "user_id": uuid4(),
        "tags": []
    }
    if (response := ReminderSchema.model_validate(reminder)):
        return response
    raise
