import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from backend.control_plane.db.models import Reminder


# Импортируем модели и схемы, которые будем проверять/использовать

# Импортируй схемы запросов и ответов, если они у тебя есть
# from app.schemas.reminder import ReminderToEditRequestSchema, ReminderSchema, ...

# Тесты будут автоматически использовать фикстуры из conftest.py
# Например, client, db_session, test_user, test_reminder

@pytest.mark.asyncio
async def test_reminder_edit(
    client: httpx.AsyncClient, # Получаем клиента из фикстуры
    database: AsyncSession,   # Получаем сессию БД из фикстуры
    test_reminder: Reminder,  # Получаем тестовое напоминание из фикстуры
    auth_user: dict,
):
    """Тест ручки редактирования напоминания (POST /reminder/{reminder_id}/edit)."""
    reminder_id = str(test_reminder.id) # Убедись, что ID в URL - строка
    updated_text = "Текст напоминания обновлен по-братски"

    # Подготавливаем тело запроса согласно ReminderToEditRequestSchema
    # Предполагаем, что схема ожидает только 'text' в теле, а ID берется из URL
    request_body = {"text": updated_text}
    # Если схема ожидает ID и в теле, используй:
    # request_body = {"id": reminder_id, "text": updated_text} # Проверь свою схему!
    response = await client.post(
        f"/v1/reminder/{reminder_id}",
        json=request_body,
        headers=auth_user
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

    assert response.status_code == 200

    # Проверяем данные в ответе API
    data = response.json()
    assert data["id"] == reminder_id
    assert data["text"] == updated_text
    # Можешь добавить проверки других полей, например updated_at
    assert data["updated_at"] is not None # Проверяем, что поле обновилось
    # assert datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00')) > test_reminder.updated_at # Более точная проверка времени, если часовые пояса ровно обрабатываются

    # Проверяем, что данные действительно обновились в базе
    updated_reminder_in_db = await database.get(Reminder, test_reminder.id)
    assert updated_reminder_in_db is not None
    assert updated_reminder_in_db.text == updated_text
    assert updated_reminder_in_db.updated_at > test_reminder.updated_at


@pytest.mark.asyncio
async def test_reminder_delete(
    client: httpx.AsyncClient,
    database: AsyncSession,
    test_reminder: Reminder
):
    """Тест ручки удаления напоминания (DELETE /reminder/{reminder_id})."""
    reminder_id = str(test_reminder.id)

    # Для DELETE обычно тело запроса не нужно, ID берется из URL
    response = await client.delete(f"/reminder/{reminder_id}")

    print(f"Response status: {response.status_code}")
    # print(f"Response body: {response.text}") # 204 No Content обычно без тела

    assert response.status_code == 204  # 204 No Content - стандарт для успешного удаления без возврата данных

    # Проверяем, что напоминание удалено из базы
    deleted_reminder_in_db = await database.get(Reminder, test_reminder.id)
    assert deleted_reminder_in_db is None  # Напоминание должно быть удалено


@pytest.mark.asyncio
async def test_reminder_to_complete(
        client: httpx.AsyncClient,
        database: AsyncSession,
        test_reminder: Reminder
):
    """Тест ручки отметки напоминания как выполненного (POST /reminder/{reminder_id}/complete)."""
    reminder_id = str(test_reminder.id)

    # Для complete тоже, вероятно, тело запроса не нужно, ID берется из URL
    response = await client.post(f"/reminder/{reminder_id}/complete")

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

    assert response.status_code == 200

    # Проверяем данные в ответе API
    data = response.json()
    assert data["id"] == reminder_id
    assert data["is_completed"] is True
    assert data["updated_at"] is not None  # Поле обновления должно измениться

    # Проверяем, что статус действительно обновился в базе
    completed_reminder_in_db = await database.get(Reminder, test_reminder.id)
    assert completed_reminder_in_db is not None
    assert completed_reminder_in_db.is_completed is True
    assert completed_reminder_in_db.updated_at > test_reminder.updated_at


@pytest.mark.asyncio
async def test_reminder_postpone(
        client: httpx.AsyncClient,
        db_session: AsyncSession,
        test_reminder: Reminder
):
    """Тест ручки откладывания напоминания (POST /reminder/{reminder_id}/postpone)."""
    reminder_id = str(test_reminder.id)
    time_delta_seconds = 3600  # Отложить на 1 час

    # Подготавливаем тело запроса согласно ReminderToEditTimeRequestSchema
    # Предполагаем, что схема ожидает 'time_delta' (в секундах) в теле
    request_body = {"time_delta": time_delta_seconds}
    # Если схема ожидает ID и в теле, используй:
    # request_body = {"id": reminder_id, "time_delta": time_delta_seconds} # Проверь свою схему!

    # Сохраняем оригинальное время планирования для проверки
    original_scheduled_at = test_reminder.scheduled_at

    response = await client.post(
        f"/reminder/{reminder_id}/postpone",
        json=request_body
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

    assert response.status_code == 200

    # Проверяем данные в ответе API
    data = response.json()
    assert data["id"] == reminder_id
    assert data["updated_at"] is not None  # Поле обновления должно измениться

    # Проверяем, что scheduled_at обновилось и примерно на time_delta
    # Преобразуем строку времени из JSON в объект datetime
    updated_scheduled_at_from_api = datetime.fromisoformat(
        data["scheduled_at"].replace('Z', '+00:00'))  # Учитываем возможный 'Z' в конце ISO формата

    # Проверяем, что новое время примерно равно старому + дельта
    expected_scheduled_at = original_scheduled_at + timedelta(seconds=time_delta_seconds)
    # Используем небольшую дельту для сравнения времени, т.к. могут быть миллисекунды или точность float
    time_tolerance = timedelta(seconds=1)  # Допустимое отклонение в 1 секунду
    assert expected_scheduled_at - time_tolerance <= updated_scheduled_at_from_api <= expected_scheduled_at + time_tolerance

    # Проверяем, что данные действительно обновились в базе
    postponed_reminder_in_db = await db_session.get(Reminder, test_reminder.id)
    assert postponed_reminder_in_db is not None
    assert postponed_reminder_in_db.scheduled_at == updated_scheduled_at_from_api  # Сравниваем с тем, что вернул API, или напрямую с ожидаемым значением
    assert postponed_reminder_in_db.updated_at > test_reminder.updated_at


# Добавь тесты для случаев ошибок, например, напоминание не найдено (404)
@pytest.mark.asyncio
async def test_reminder_not_found(client: httpx.AsyncClient):
    """Тест на случай, когда напоминание не найдено (например, при редактировании)."""
    non_existent_id = "non_existent_reminder_id"
    response = await client.post(
        f"/reminder/{non_existent_id}/",
        json={"text": "Trying to update non-existent"}
    )
    assert response.status_code == 404  # Или какой у тебя код для Not Found

    response = await client.delete(f"/reminder/{non_existent_id}")
    assert response.status_code == 404

    response = await client.post(f"/reminder/{non_existent_id}/complete")
    assert response.status_code == 404

    response = await client.post(
        f"/reminder/{non_existent_id}/postpone",
        json={"time_delta": 3600}
    )
    assert response.status_code == 404