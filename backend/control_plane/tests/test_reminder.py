import pytest
import httpx
from fastapi import FastAPI
from fastapi.routing import APIRoute
from typing import Any, Callable, Dict

from backend.control_plane.routes import reminder_router
# Импортируйте ваш роутер и зависимости
from backend.control_plane.service.reminder_service import RemindersService, \
    get_reminder_service  # или как у вас называется сервис
from backend.control_plane.utils.auth import get_authorized_user
from backend.control_plane.schemas.user import UserSchema


# --- Моки и заглушки (Mocks & Stubs) ---

class MockReminderService:
    """Мок сервиса напоминаний для тестов."""
    async def reminder_create(self, user_id: str, request: Any) -> Any: # Замените Any на реальный тип ReminderSchema, если он известен
        return {"id": "mock_reminder_id", "user_id": user_id, "text": request.text, "is_completed": False}

    async def reminders_get_active(self, user_id: str) -> list[Any]: # Замените Any на реальный тип ReminderSchema, если он известен
        return [{"id": "mock_reminder_id_1", "user_id": user_id, "text": "Mock Reminder 1", "is_completed": False},
                {"id": "mock_reminder_id_2", "user_id": user_id, "text": "Mock Reminder 2", "is_completed": False}]

    async def reminder_update(self, user_id: str, reminder: Any) -> Any: # Замените Any на реальный тип ReminderSchema, если он известен
        return {"id": reminder.id, "user_id": user_id, "text": reminder.text, "is_completed": False}

    async def reminder_delete(self, user_id: str, reminder: Any) -> None:
        pass  # Ничего не возвращаем при удалении

    async def mark_as_complete(self, user_id: str, reminder: Any) -> Any: # Замените Any на реальный тип ReminderSchema, если он известен
        return {"id": reminder.id, "user_id": user_id, "text": "Mock Reminder Completed", "is_completed": True}

    async def postpone(self, user_id: str, reminder: Any) -> Any: # Замените Any на реальный тип ReminderSchema, если он известен
        return {"id": reminder.id, "user_id": user_id, "text": "Mock Reminder Postponed", "is_completed": False}


async def mock_get_reminder_service() -> MockReminderService:
    """Заглушка для сервиса напоминаний."""
    return MockReminderService()

async def mock_get_authorized_user() -> UserSchema:
    """Заглушка для авторизованного пользователя."""
    return UserSchema(id="test_user_id", username="testuser", email="test@example.com") # Пример UserSchema


# --- Функция для создания тестового FastAPI приложения ---

def create_test_app() -> FastAPI:
    """Создает тестовое FastAPI приложение с переопределенными зависимостями."""
    app = FastAPI()
    # Переопределение зависимостей для тестов:
    app.dependency_overrides[get_reminder_service] = mock_get_reminder_service
    app.dependency_overrides[get_authorized_user] = mock_get_authorized_user
    app.include_router(reminder_router) # Включаем ваш роутер
    return app


# --- Тестовые функции ---

@pytest.mark.asyncio
async def test_reminder_add():
    """Тест ручки создания напоминания (POST /reminder/)."""
    app = create_test_app()
    async with httpx.AsyncClient(base_url="http://test") as client:
        response = await client.post(
            "/reminder/",
            json={"text": "Test reminder text"} # Пример тела запроса, адаптируйте под вашу ReminderAddSchemaRequest
        )
    assert response.status_code == 200  # или 201, как указано в responses в роутере
    data = response.json()
    assert data["text"] == "Test reminder text"
    assert data["user_id"] == "test_user_id"
    assert "id" in data


@pytest.mark.asyncio
async def test_reminders_get_active():
    """Тест ручки получения активных напоминаний (GET /reminder/)."""
    app = create_test_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/reminder/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # Ожидаем как минимум 2 моковых напоминания
    assert all(["text" in item for item in data])


@pytest.mark.asyncio
async def test_reminder_edit():
    """Тест ручки редактирования напоминания (POST /reminder/{reminder_id})."""
    app = create_test_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reminder/test_reminder_id", # Используйте корректный reminder_id
            json={"id": "test_reminder_id", "text": "Updated reminder text"} # Пример тела запроса, адаптируйте под ReminderToEditRequestSchema
        )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Updated reminder text"
    assert data["id"] == "test_reminder_id"


@pytest.mark.asyncio
async def test_reminder_delete():
    """Тест ручки удаления напоминания (DELETE /reminder/{reminder_id})."""
    app = create_test_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            "/reminder/test_reminder_id", # Используйте корректный reminder_id
            json={"id": "test_reminder_id"} # Пример тела запроса, адаптируйте под ReminderToDeleteRequestSchema
        )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reminder_to_complete():
    """Тест ручки отметки напоминания как выполненного (POST /reminder/{reminder_id}/complete)."""
    app = create_test_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reminder/test_reminder_id/complete", # Используйте корректный reminder_id
            json={"id": "test_reminder_id"} # Пример тела запроса, адаптируйте под ReminderMarkAsCompleteRequestSchema
        )
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] is True


@pytest.mark.asyncio
async def test_reminder_postpone():
    """Тест ручки откладывания напоминания (POST /reminder/{reminder_id}/postpone)."""
    app = create_test_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reminder/test_reminder_id/postpone", # Используйте корректный reminder_id
            json={"id": "test_reminder_id", "time_delta": 3600} # Пример тела запроса, адаптируйте под ReminderToEditTimeRequestSchema
        )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Mock Reminder Postponed" # Проверяем, что моковый сервис отработал верно